"""
预处理模块 — 面部清晰度量化检测
--------------------------------
在视频送审大模型之前，用 OpenCV 逐帧量化分析：
1. 人脸区域清晰度（拉普拉斯方差）
2. 背景区域清晰度
3. 面部/背景清晰度比值
4. 帧间清晰度波动

生成结构化预处理报告，注入提示词上下文。

抽帧策略（v4.1）：
- 目标密度约每 2 秒 1 帧，最少 4 帧
- 时间窗：起点跳过片头（前 1 秒或时长的 8%），终点覆盖到结尾前 0.5 秒
- 每帧加 ±1/3 间隔的随机抖动（种子=文件哈希，可复现），避免与剪辑节奏系统性对齐
- 长视频动态放宽帧数上限（保证采样间隔不超过约 3 秒），绝对上限 48 帧
- 时间戳取 seek 后真实位置（消除关键帧对齐误差）
- 帧统一缩放至最长边 ≤1600px（控制内存、统一不同分辨率视频的清晰度尺度）
"""

import hashlib
import logging
import math
import os
import random
import threading
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# 人脸检测器（OpenCV Haar Cascade）
# CascadeClassifier 非线程安全：多视频并发预处理时需加锁
_FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_face_detector = cv2.CascadeClassifier(_FACE_CASCADE_PATH)
_face_lock = threading.Lock()

# 清晰度异常阈值：面部/背景清晰度比值低于此值视为可疑
BLUR_RATIO_THRESHOLD = 0.50  # 恢复敏感度（v4.0原值0.55，微调至0.50平衡点）
# 帧间清晰度波动阈值（标准差/均值）
FLUCTUATION_THRESHOLD = 0.25  # 恢复敏感度（v4.0原值0.20，微调至0.25）

# phys 子分截断（v5.12）：加权 z 和天然无界，病态样本可达 19（如 F96=18.97、
# 真实 96=13.02），融合前压到 ±3 防止单一样本主导规则/融合器
PHYS_SCORE_CLIP = 3.0

# ---- 抽帧策略参数 (v4.1) ----
TARGET_INTERVAL = 2.0            # 目标采样间隔（秒）：约每 2 秒 1 帧
MIN_FRAMES = 4                   # 最少抽帧数（极短视频保底）
DEFAULT_MAX_FRAMES = 16          # 默认帧数上限（长视频会动态放宽）
LONG_VIDEO_MAX_INTERVAL = 3.0    # 长视频最长采样间隔（秒）
ABSOLUTE_MAX_FRAMES = 48         # 绝对帧数上限（约束内存）
START_SKIP_SECONDS = 1.0         # 跳过片头秒数，实际取 min(该值, 时长*8%)
END_MARGIN_SECONDS = 0.5         # 最后一帧距视频结尾的秒数
JITTER_FRACTION = 1 / 3          # 抖动幅度 = 采样间隔的 1/3
FRAME_MAX_DIM = 1600             # 存储帧最长边（统一分辨率尺度 + 控制内存）
FACE_RETRY_DELTA = 0.4           # 无脸帧就近补采偏移（秒）
FACE_RETRY_MAX = 6               # 每视频最多补采次数（约束病态视频的额外开销）
MIN_STEP_SECONDS = 0.3           # 两帧最小时间差（秒），小于此值视为重复帧


def _resize_for_analysis(frame: np.ndarray) -> np.ndarray:
    """将帧缩放至最长边 ≤ FRAME_MAX_DIM，统一分辨率尺度并控制内存。"""
    h, w = frame.shape[:2]
    if max(w, h) <= FRAME_MAX_DIM:
        return frame
    scale = FRAME_MAX_DIM / max(w, h)
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def _read_frame_at(cap: cv2.VideoCapture, ts: float) -> tuple[float, np.ndarray] | None:
    """seek 到 ts 秒并读取一帧，返回 (实际时间戳, 缩放后图像)；失败返回 None。"""
    cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
    ret, frame = cap.read()
    if not ret or frame is None or frame.size == 0:
        return None
    actual_ts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
    return actual_ts, _resize_for_analysis(frame)


def _extract_frames(video_path: str, max_frames: int = DEFAULT_MAX_FRAMES) -> list[tuple[float, np.ndarray]]:
    """
    从视频中采样分析帧（v4.1 策略）。

    - 时间窗：[start, end]：start 跳过片头（min(1s, 时长*8%)），end 覆盖到结尾前 0.5s
    - 帧数：目标约每 2 秒 1 帧（最少 4 帧）；长视频动态放宽上限，
      保证采样间隔不超过约 3 秒，绝对上限 48 帧
    - 抖动：每帧加 ±1/3 间隔的随机偏移（种子=文件哈希，可复现）
    - 返回 [(实际时间戳_秒, BGR图像), ...]，时间戳取 seek 后的真实位置
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning("无法打开视频: %s", video_path)
        return []

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0

        duration = total_frames / fps
        if duration <= 0:
            return []

        # ---- 时间窗：跳片头，覆盖到结尾 ----
        start = min(START_SKIP_SECONDS, duration * 0.08)
        end = duration - END_MARGIN_SECONDS
        if end <= start:
            end = duration  # 极短视频：退化为覆盖整个视频
        window = end - start

        # ---- 帧数：目标每 2 秒 1 帧 ----
        sample_count = round(window / TARGET_INTERVAL) + 1
        sample_count = max(MIN_FRAMES, sample_count)
        # 长视频动态放宽上限：保证间隔 ≤ LONG_VIDEO_MAX_INTERVAL
        dynamic_max = max(max_frames, math.ceil(duration / LONG_VIDEO_MAX_INTERVAL))
        sample_count = min(sample_count, dynamic_max, ABSOLUTE_MAX_FRAMES)

        # ---- 均匀网格 + 随机抖动（可复现）----
        base = np.linspace(start, end, sample_count)
        interval = window / max(1, sample_count - 1)
        jitter = JITTER_FRACTION * interval
        # 内容哈希而非路径：同一视频的任意副本（chunk 目录等）必须得到相同采样帧集
        _h = hashlib.md5()
        with open(video_path, "rb") as _fp:
            _h.update(_fp.read(65536))
        _h.update(f"{os.path.getsize(video_path)}|{total_frames}|{fps:.3f}"
                  .encode("utf-8"))
        seed = int(_h.hexdigest(), 16) % (2 ** 32)
        rng = random.Random(seed)
        timestamps = sorted(
            np.clip(base + [rng.uniform(-jitter, jitter) for _ in base], start, end)
        )

        # ---- 读取帧（跳过重复帧，时间戳取真实位置）----
        frames = []
        last_ts = -10.0
        for ts in timestamps:
            got = _read_frame_at(cap, ts)
            if got is None:
                continue
            actual_ts, frame = got
            # 关键帧对齐导致两次 seek 落到同一帧时，跳过重复
            if actual_ts - last_ts < MIN_STEP_SECONDS:
                continue
            last_ts = actual_ts
            frames.append((actual_ts, frame))
    finally:
        cap.release()

    logger.debug("  [预处理] %s: 提取 %d/%d 帧 (时长 %.1fs, FPS %.1f)",
                 Path(video_path).name, len(frames), sample_count, duration, fps)
    return frames


DENSE_RESCAN_STEP = 0.5          # 兜底重扫采样步长（秒）
DENSE_RESCAN_MAX_FRAMES = 40     # 兜底重扫帧数上限
DENSE_RESCAN_MIN_HITS = 2        # 兜底重扫最少命中帧数（防背景误检）


def _dense_relaxed_frames(video_path: str) -> list:
    """
    严格参数整片零检出时的兜底：宽松参数每 0.5s 密集重扫，
    返回 [(实际时间戳, 帧, 人脸框), ...]；命中帧过少或尺寸波动过大
    （疑似背景误检）时返回空列表。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    hits = []
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = total_frames / fps if fps > 0 else 0.0
        if duration <= 0:
            return []
        start = min(START_SKIP_SECONDS, duration * 0.08)
        end = max(start + 0.5, duration - END_MARGIN_SECONDS)
        timestamps = list(np.arange(start, end, DENSE_RESCAN_STEP))[:DENSE_RESCAN_MAX_FRAMES]
        sizes = []
        for ts in timestamps:
            got = _read_frame_at(cap, ts)
            if got is None:
                continue
            actual_ts, frame = got
            rect = _detect_face_relaxed(frame)
            if rect is None:
                continue
            hits.append((actual_ts, frame, rect))
            sizes.append(rect[2])
        if len(hits) >= DENSE_RESCAN_MIN_HITS and sizes:
            if float(np.std(sizes)) / (float(np.mean(sizes)) + 1e-6) <= 0.6:
                logger.warning("[预处理] %s: 严格参数零检出，宽松兜底重扫命中 %d 帧",
                               Path(video_path).name, len(hits))
                return hits
        return []
    finally:
        cap.release()


def _read_nearby_with_face(cap: cv2.VideoCapture, ts: float,
                           delta: float = FACE_RETRY_DELTA):
    """
    无脸帧就近补采：用已打开的 cap 在 ts±delta 处重试读取并检测人脸
    （转头/遮挡导致漏检时用）。返回 (实际时间戳, 图像, 人脸框) 或 None。
    """
    for offset in (delta, -delta):
        got = _read_frame_at(cap, max(0.0, ts + offset))
        if got is None:
            continue
        actual_ts, frame = got
        face_rect = _detect_face(frame)
        if face_rect is not None:
            return actual_ts, frame, face_rect
    return None


def _detect_face(frame: np.ndarray) -> tuple[int, int, int, int] | None:
    """检测最大人脸区域，返回 (x, y, w, h) 或 None。"""
    h, w = frame.shape[:2]

    # 处理极端尺寸：过大的帧缩小，过小的帧跳过
    max_dim = 1920
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        h, w = frame.shape[:2]

    if min(w, h) < 100:
        return None

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 动态调整 minSize 以适应不同分辨率
    min_face = max(60, min(w, h) // 8)

    try:
        with _face_lock:
            faces = _face_detector.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5,
                minSize=(min_face, min_face),
                maxSize=(min(w, h) // 2, min(w, h) // 2)
            )
    except cv2.error:
        # Haar cascade 内部错误（如 scaleIdx 断言失败），降级尝试
        try:
            # 用更宽松的参数重试
            with _face_lock:
                faces = _face_detector.detectMultiScale(
                    gray, scaleFactor=1.2, minNeighbors=3,
                    minSize=(min_face, min_face)
                )
        except cv2.error:
            return None

    if len(faces) == 0:
        return None

    # 取面积最大的人脸（按原始帧坐标缩放回原尺寸）
    best = max(faces, key=lambda r: r[2] * r[3])
    if max(w, h) > max_dim:
        inv_scale = 1.0 / scale
        best = (best[0] * inv_scale, best[1] * inv_scale,
                best[2] * inv_scale, best[3] * inv_scale)
    # 统一返回纯元组（detectMultiScale 返回 numpy 行，直接返回会破坏 None 判断链）
    return tuple(int(v) for v in best)


def _detect_face_relaxed(frame: np.ndarray) -> tuple[int, int, int, int] | None:
    """
    宽松参数人脸检测（严格参数漏检时的兜底，小脸/侧脸召回优先）。
    与 _detect_face 相同的尺寸处理与坐标约定，minSize 下限降至 40。
    """
    h, w = frame.shape[:2]
    scale = 1.0
    if max(w, h) > 1920:
        scale = 1920.0 / max(w, h)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        h, w = frame.shape[:2]
    if min(w, h) < 100:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    try:
        with _face_lock:
            faces = _face_detector.detectMultiScale(
                gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40),
                maxSize=(min(w, h) // 2, min(w, h) // 2))
    except cv2.error:
        return None
    if len(faces) == 0:
        return None
    best = max(faces, key=lambda r: r[2] * r[3])
    if scale != 1.0:
        inv = 1.0 / scale
        best = (best[0] * inv, best[1] * inv,
                best[2] * inv, best[3] * inv)
    return tuple(int(v) for v in best)


def _sharpeness_laplacian(roi: np.ndarray) -> float:
    """
    计算区域清晰度（拉普拉斯方差）。
    值越大越清晰，<50 通常表示模糊，>200 表示锐利。
    """
    if roi.size == 0 or roi.shape[0] < 10 or roi.shape[1] < 10:
        return 0.0
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


def _sample_background_regions(frame: np.ndarray, face_rect: tuple,
                                num_samples: int = 4) -> list[np.ndarray]:
    """
    在人脸区域之外采样背景区域。
    返回背景 ROI 列表。
    """
    h, w = frame.shape[:2]
    fx, fy, fw, fh = face_rect

    # 定义 4 个角区域（避开人脸）
    margin = 20
    regions = [
        (margin, margin, w // 4, h // 4),                          # 左上
        (w - w // 4 - margin, margin, w // 4, h // 4),              # 右上
        (margin, h - h // 4 - margin, w // 4, h // 4),              # 左下
        (w - w // 4 - margin, h - h // 4 - margin, w // 4, h // 4), # 右下
    ]

    samples = []
    for rx, ry, rw, rh in regions:
        # 避免与人脸区域重叠
        if (rx < fx + fw and rx + rw > fx and ry < fy + fh and ry + rh > fy):
            continue
        roi = frame[ry:ry + rh, rx:rx + rw]
        if roi.size > 0:
            samples.append(roi)

    return samples[:num_samples]


def _sample_body_skin(frame: np.ndarray, face_rect: tuple) -> np.ndarray | None:
    """
    采样颈部/身体皮肤区域（面部下方）。
    用于判断是"仅面部模糊（换脸）"还是"全局柔化（美颜/打光）"。
    返回颈部皮肤 ROI 或 None。
    """
    h, w = frame.shape[:2]
    fx, fy, fw, fh = face_rect

    # 颈部区域：人脸下方约 0.3-0.8 倍人脸高度
    neck_y1 = fy + fh + int(fh * 0.05)
    neck_y2 = min(h, fy + fh + int(fh * 0.9))
    neck_x1 = fx + int(fw * 0.2)
    neck_x2 = fx + int(fw * 0.8)

    if neck_y2 <= neck_y1 or neck_x2 <= neck_x1:
        return None

    roi = frame[neck_y1:neck_y2, neck_x1:neck_x2]
    if roi.size > 0 and roi.shape[0] > 15 and roi.shape[1] > 15:
        return roi
    return None


def analyze_video(video_path: str) -> dict:
    """
    分析视频面部清晰度。

    返回:
        dict:
            face_sharpness_mean: 面部平均清晰度
            bg_sharpness_mean: 背景平均清晰度
            ratio_mean: 面部/背景清晰度比值均值
            ratio_min: 最小比值（最可疑帧）
            fluctuation: 帧间面部清晰度波动系数
            blur_frames: 清晰度比值低于阈值的帧数
            total_frames: 有效检测帧数
            verdict: "正常" | "可疑"
            summary: 中文摘要
    """
    frames = _extract_frames(video_path)
    if not frames:
        return {"error": "无法提取帧", "verdict": "无法判定", "summary": ""}

    # 视频时长（供先验模型使用）
    duration = 0.0
    try:
        probe = cv2.VideoCapture(video_path)
        if probe.isOpened():
            total_f = int(probe.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = probe.get(cv2.CAP_PROP_FPS) or 30.0
            duration = total_f / fps
        probe.release()
    except Exception:
        pass

    face_sharpness_vals = []
    bg_sharpness_vals = []
    neck_sharpness_vals = []
    ratios = []
    face_neck_ratios = []
    blur_count = 0
    sample_details = []

    # 无脸帧就近补采用的惰性 capture：整个视频只打开一次，避免每漏检一帧都重开视频
    retry_cap = None
    retries_left = FACE_RETRY_MAX
    for ts, frame in frames:
        face_rect = _detect_face(frame)
        if face_rect is None and retries_left > 0:
            if retry_cap is None:
                retry_cap = cv2.VideoCapture(video_path)
                if not retry_cap.isOpened():
                    retry_cap.release()
                    retry_cap = None
            if retry_cap is not None:
                # 转头/遮挡导致的漏检，±0.4s 重试一次
                retries_left -= 1
                retried = _read_nearby_with_face(retry_cap, ts)
                if retried is not None:
                    ts, frame, face_rect = retried
        if face_rect is None:
            continue

        fx, fy, fw, fh = face_rect
        face_roi = frame[fy:fy + fh, fx:fx + fw]

        face_sharp = _sharpeness_laplacian(face_roi)
        if face_sharp <= 0:
            continue

        bg_regions = _sample_background_regions(frame, face_rect)
        if not bg_regions:
            continue

        bg_sharp = np.mean([_sharpeness_laplacian(r) for r in bg_regions])
        if bg_sharp <= 0:
            continue

        # 颈部皮肤采样（区分"仅面部模糊" vs "全局柔化"）
        neck_roi = _sample_body_skin(frame, face_rect)
        neck_sharp = _sharpeness_laplacian(neck_roi) if neck_roi is not None else None

        ratio = face_sharp / bg_sharp
        face_sharpness_vals.append(face_sharp)
        bg_sharpness_vals.append(bg_sharp)
        ratios.append(ratio)

        if neck_sharp is not None and neck_sharp > 0:
            neck_sharpness_vals.append(neck_sharp)
            face_neck_ratios.append(face_sharp / neck_sharp)

        if ratio < BLUR_RATIO_THRESHOLD:
            blur_count += 1
            neck_info = ""
            if neck_sharp is not None and neck_sharp > 0:
                fn_ratio = face_sharp / neck_sharp
                neck_info = f", 颈部清晰度={neck_sharp:.0f}, 面颈比={fn_ratio:.2f}"
            sample_details.append(
                f"  ⚠ t={ts:.1f}s: 面部清晰度={face_sharp:.0f}, 背景清晰度={bg_sharp:.0f}, "
                f"比值={ratio:.2f} (低于阈值{BLUR_RATIO_THRESHOLD}){neck_info}"
            )

    if retry_cap is not None:
        retry_cap.release()

    # ---- 兜底重扫：严格参数整片零检出时，用宽松参数密集重扫（小脸/侧脸）----
    if len(ratios) == 0:
        for actual_ts, frame, face_rect in _dense_relaxed_frames(video_path):
            fx, fy, fw, fh = face_rect
            face_roi = frame[fy:fy + fh, fx:fx + fw]
            face_sharp = _sharpeness_laplacian(face_roi)
            if face_sharp <= 0:
                continue
            bg_regions = _sample_background_regions(frame, face_rect)
            if not bg_regions:
                continue
            bg_sharp = np.mean([_sharpeness_laplacian(r) for r in bg_regions])
            if bg_sharp <= 0:
                continue
            neck_roi = _sample_body_skin(frame, face_rect)
            neck_sharp = _sharpeness_laplacian(neck_roi) if neck_roi is not None else None
            ratio = face_sharp / bg_sharp
            face_sharpness_vals.append(face_sharp)
            bg_sharpness_vals.append(bg_sharp)
            ratios.append(ratio)
            if neck_sharp is not None and neck_sharp > 0:
                neck_sharpness_vals.append(neck_sharp)
                face_neck_ratios.append(face_sharp / neck_sharp)
            if ratio < BLUR_RATIO_THRESHOLD:
                blur_count += 1
                neck_info = ""
                if neck_sharp is not None and neck_sharp > 0:
                    fn_ratio = face_sharp / neck_sharp
                    neck_info = f", 颈部清晰度={neck_sharp:.0f}, 面颈比={fn_ratio:.2f}"
                sample_details.append(
                    f"  ⚠ t={actual_ts:.1f}s: 面部清晰度={face_sharp:.0f}, "
                    f"背景清晰度={bg_sharp:.0f}, 比值={ratio:.2f} "
                    f"(低于阈值{BLUR_RATIO_THRESHOLD}){neck_info}"
                )

    total = len(ratios)
    if total == 0:
        return {"error": "未检测到人脸", "verdict": "无法判定", "summary": ""}

    face_mean = np.mean(face_sharpness_vals)
    bg_mean = np.mean(bg_sharpness_vals)
    ratio_mean = np.mean(ratios)
    ratio_min = np.min(ratios)
    ratio_std = np.std(ratios)
    fluctuation = ratio_std / ratio_mean if ratio_mean > 0 else 0

    # 面颈比分析：面部 vs 颈部皮肤清晰度
    neck_mean = np.mean(neck_sharpness_vals) if neck_sharpness_vals else 0
    face_neck_ratio_mean = np.mean(face_neck_ratios) if face_neck_ratios else 1.0

    # 判断是"仅面部模糊"还是"全局柔化"
    is_global_softening = False
    if neck_mean > 0:
        # 面颈比 > 0.85 才认为是真正的全局柔化（面部与身体清晰度高度一致）
        if face_neck_ratio_mean > 0.85:
            is_global_softening = True
        # 面颈比 < 0.80 则面部明显比颈部模糊 → 换脸可疑
        face_only_blur = (face_neck_ratio_mean < 0.80)
    else:
        face_only_blur = False

    # 判定逻辑
    danger_signals = 0
    if ratio_mean < BLUR_RATIO_THRESHOLD:
        danger_signals += 2
    elif ratio_mean < 0.65:
        danger_signals += 1
    if blur_count >= total * 0.3:
        danger_signals += 2
    elif blur_count >= total * 0.15:
        danger_signals += 1
    if fluctuation > FLUCTUATION_THRESHOLD:
        danger_signals += 1

    # 不再因"全局柔化"降级——让模型结合视觉判断，而非预处理单方面压分
    # （移除旧的 danger_signals 上限逻辑）

    if danger_signals >= 3:
        verdict = "面部明显比背景模糊（注意：美颜滤镜与换脸蒙版均可导致此现象，不构成单独证据）"
    elif danger_signals >= 2:
        if face_only_blur:
            verdict = "面部比背景和颈部都模糊（美颜仅处理面部时也会如此，不构成单独证据）"
        else:
            verdict = "面部比背景略模糊（美颜/柔光常见，不构成单独证据）"
    elif danger_signals >= 1:
        if is_global_softening:
            verdict = "面颈清晰度一致，提示全局柔化处理（美颜/柔光）"
        else:
            verdict = "面部稍柔于背景，差异在美颜/柔光正常范围内"
    else:
        verdict = "面部与背景清晰度一致"

    # 构建摘要（v5.0 中性化：只呈现数据与客观解读，不做定罪式预判）
    summary = (
        f"【预处理】面部清晰度量化检测报告（量化参考，不代表结论）\n"
        f"  抽帧策略: 约每{TARGET_INTERVAL:.0f}秒1帧(±抖动)，覆盖全程\n"
        f"  有效检测帧数: {total}\n"
        f"  面部平均清晰度: {face_mean:.1f} (拉普拉斯方差)\n"
        f"  背景平均清晰度: {bg_mean:.1f}\n"
        f"  面部/背景清晰度比值: 均值={ratio_mean:.2f}, 最低={ratio_min:.2f}, 标准差={ratio_std:.2f}\n"
        f"  帧间波动系数: {fluctuation:.2f} (阈值={FLUCTUATION_THRESHOLD})\n"
        f"  清晰度异常帧数: {blur_count}/{total}"
    )
    if neck_mean > 0:
        summary += (
            f"\n  颈部皮肤清晰度: {neck_mean:.1f}\n"
            f"  面部/颈部清晰度比值: {face_neck_ratio_mean:.2f}"
            f" {'(面颈一致→更符合全局美颜/柔光)' if is_global_softening else '(面比颈模糊→美颜与换脸均可导致，需视觉证据区分)' if face_only_blur else ''}"
        )
    if sample_details:
        summary += "\n  清晰度异常帧详情:"
        for detail in sample_details[:6]:
            summary += f"\n{detail}"

    summary += f"\n  预处理判定: {verdict}"

    # 根据结果给出不同级别的客观提示（不做定罪引导）
    if danger_signals >= 3:
        summary += (
            '\n\n  【数据说明】清晰度数据显示面部明显比背景模糊。'
            '该现象在美颜滤镜视频中同样常见，请勿单独作为伪造证据，'
            '需结合视觉上的边界断层、肤色割裂、时间突变等硬证据判断。'
        )
    elif danger_signals >= 2:
        if face_only_blur:
            summary += (
                '\n\n  【数据说明】面部清晰度低于背景和颈部。'
                '美颜仅作用于面部时会产生同样数据，请结合'
                '#6 唇形同步、#9 眨眼行为、#10 微表情等生物信号与视觉证据判断。'
            )
        else:
            summary += (
                '\n\n  【数据说明】面部清晰度略低于背景，处于美颜/柔光常见范围内。'
                '请以视觉证据与生物信号维度（#6 唇形、#9 眨眼、#10 微表情）为主要判断依据。'
            )
    elif is_global_softening:
        summary += (
            '\n\n  【数据说明】面部与颈部清晰度一致，符合画面整体柔化'
            '（美颜滤镜/柔光）的数据特征，而非仅面部被处理。'
        )
    else:
        summary += (
            '\n\n  【数据说明】清晰度差异处于正常范围。'
            '请以生物信号维度（#6 唇形同步、#9 眨眼行为、#10 微表情）为主要判断依据。'
        )

    # ---- 物理一致性定量特征（密集扫描，供先验模型） ----
    try:
        phys = _dense_physical_scan(video_path)
    except Exception as e:
        logger.warning("物理特征扫描异常 %s: %s", Path(video_path).name, str(e))
        phys = {}

    # ---- 唇同步一致性特征 ----
    try:
        lip = _lip_sync_scan(video_path)
    except Exception as e:
        logger.warning("唇同步扫描异常 %s: %s", Path(video_path).name, str(e))
        lip = {}
    phys.update(lip)

    result = {
        "total_frames": total,
        "face_sharpness_mean": round(face_mean, 1),
        "bg_sharpness_mean": round(bg_mean, 1),
        "neck_sharpness_mean": round(neck_mean, 1) if neck_mean > 0 else None,
        "ratio_mean": round(ratio_mean, 2),
        "ratio_min": round(ratio_min, 2),
        "ratio_std": round(ratio_std, 2),
        "face_neck_ratio": round(face_neck_ratio_mean, 2) if neck_sharpness_vals else None,
        "fluctuation": round(fluctuation, 2),
        "blur_frames": blur_count,
        "is_global_softening": is_global_softening,
        "verdict": verdict,
        "summary": summary,
        "duration": round(duration, 2),
    }
    result.update(phys)
    return result


# ==================================================================
# 先验模型：基于 200 个已标注视频拟合的 P(伪造|预处理特征)
# ==================================================================

_PRIOR_MODEL_PATH = Path(__file__).resolve().parent / "prior_model.json"
_PRIOR_V16_PATH = Path(__file__).resolve().parent / "prior_model_v16.json"

_loaded_models: dict = {}


def _load_model(path: Path) -> dict | None:
    """加载先验模型 JSON（带进程内缓存）。文件不存在返回 None。"""
    if not path.exists():
        return None
    if path not in _loaded_models:
        import json
        with open(path, 'r', encoding='utf-8') as f:
            _loaded_models[path] = json.load(f)
    return _loaded_models[path]


def _prior_with_model(result: dict, model: dict) -> float | None:
    """按给定模型计算 P(伪造|预处理特征)。与特征表拟合约定一致。"""
    def val(key):
        v = result.get(key)
        return float(v) if v is not None else -1.0

    total = result.get('total_frames', 0)
    raw = {
        'duration': float(result.get('duration', 0.0)),
        'valid_frames': float(total),
        'face_sharp_mean': val('face_sharpness_mean'),
        'bg_sharp_mean': val('bg_sharpness_mean'),
        'neck_sharp_mean': val('neck_sharpness_mean'),
        'ratio_mean': val('ratio_mean'),
        'ratio_min': val('ratio_min'),
        'ratio_std': val('ratio_std'),
        'face_neck_ratio': val('face_neck_ratio'),
        'fluctuation': val('fluctuation'),
        'blur_frac': (result.get('blur_frames', 0) / total) if total else 0.0,
        'global_softening': 1.0 if result.get('is_global_softening') else 0.0,
        # 物理一致性特征：缺失时用 0（与特征表拟合时的缺省约定一致）
        'occl_edge_ratio': float(result.get('occl_edge_ratio', 0.0) or 0.0),
        'occl_edge_ratio_min': float(result.get('occl_edge_ratio_min', 0.0) or 0.0),
        'face_box_jitter': float(result.get('face_box_jitter', 0.0) or 0.0),
        'face_size_jitter': float(result.get('face_size_jitter', 0.0) or 0.0),
        'noise_ratio': float(result.get('noise_ratio', 0.0) or 0.0),
        'chroma_diff': float(result.get('chroma_diff', 0.0) or 0.0),
        'rot_diff_energy': float(result.get('rot_diff_energy', 0.0) or 0.0),
        'flow_consistency': float(result.get('flow_consistency', 0.0) or 0.0),
        'lip_sync_corr': float(result.get('lip_sync_corr', 0.0) or 0.0),
        'lip_sync_lag': float(result.get('lip_sync_lag', 0.0) or 0.0),
    }
    z = model.get('bias', 0.0)
    for name, mu, sd, w in zip(model['features'], model['mu'], model['sd'], model['weights']):
        x = raw.get(name, 0.0)
        sd = sd if sd > 1e-9 else 1.0
        z += w * (x - mu) / sd
    p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
    return p


def compute_prior_probability(result: dict) -> float | None:
    """
    根据标注数据拟合的先验模型（v5.2 新模型，16特征）计算 P(伪造|预处理特征)。
    模型文件不存在或无法计算时返回 None。
    """
    model = _load_model(_PRIOR_MODEL_PATH)
    if model is None:
        return None
    return _prior_with_model(result, model)


# ==================================================================
# 唇同步一致性特征（v5.5 内容特征）
# ------------------------------------------------------------------
# 音视频唇同步是换脸/面部重演最经典的内容伪影之一：
# 真实视频中嘴部运动与音频能量包络强相关；换脸/重演/配音会使
# 嘴部重绘信号与音频脱同步或弱相关。用 PyAV 解码音轨（自带
# ffmpeg 库，无需系统安装），与 10fps 嘴部运动信号做交叉相关。
# ==================================================================

LIP_SAMPLE_INTERVAL = 0.1        # 唇同步采样间隔（秒），10fps
LIP_MAX_FRAMES = 200             # 唇同步扫描帧数上限（≈20s 窗口）
LIP_AUDIO_RATE = 8000            # 音频重采样率
LIP_LAG_SAMPLES = 3              # 交叉相关滞后搜索 ±0.3s


def _lip_sync_scan(video_path: str) -> dict:
    """
    计算唇同步一致性。返回 {'lip_sync_corr': 最大交叉相关, 'lip_sync_lag': 最优滞后秒}。
    无音轨/无人脸时返回空 dict。
    """
    import av

    try:
        container = av.open(video_path)
    except Exception as e:
        logger.debug("[唇同步] 无法打开 %s: %s", Path(video_path).name, str(e))
        return {}

    # ---- 音频能量包络 ----
    audio_ts, audio_env = None, None
    try:
        a_stream = container.streams.audio[0] if container.streams.audio else None
        if a_stream is not None:
            resampler = av.AudioResampler(format='s16', layout='mono', rate=LIP_AUDIO_RATE)
            chunks = []
            t0 = None
            for frame in container.decode(a_stream):
                if t0 is None and frame.time is not None:
                    t0 = float(frame.time)
                for rf in resampler.resample(frame):
                    arr = rf.to_ndarray()
                    if arr.ndim > 1:
                        arr = arr.mean(axis=0)
                    chunks.append(arr.astype(np.float32) / 32768.0)
            if chunks:
                samples = np.concatenate(chunks)
                n = len(samples)
                audio_ts = (t0 or 0.0) + np.arange(n) / LIP_AUDIO_RATE
                # 能量包络：50ms 滑窗
                win = max(1, int(0.05 * LIP_AUDIO_RATE))
                kernel = np.ones(win) / win
                audio_env = np.convolve(np.abs(samples), kernel, mode='same')
    except Exception as e:
        logger.debug("[唇同步] 音频解码失败 %s: %s", Path(video_path).name, str(e))
    finally:
        container.close()

    if audio_env is None:
        return {}

    # ---- 嘴部运动信号（10fps 密集扫描） ----
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {}
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        duration = total_frames / fps
        if duration <= 0:
            return {}
        start = EVENT_START_SKIP
        end = max(start + 0.5, duration - 0.3)
        n = min(LIP_MAX_FRAMES, max(3, math.ceil((end - start) / LIP_SAMPLE_INTERVAL)))
        timestamps = list(np.linspace(start, end, n))

        mouth_ts, mouth_motion = [], []
        prev_gray, prev_rect = None, None
        for ts in timestamps:
            got = _read_frame_at(cap, ts)
            if got is None:
                prev_gray, prev_rect = None, None
                continue
            _, frame = got
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rect = _detect_face(frame) or _detect_face_relaxed(frame)
            if rect is not None and prev_gray is not None and prev_rect is not None:
                x, y, fw, fh = rect
                px, py, pfw, pfh = prev_rect
                # 嘴部 ROI：脸框下部中央（当前帧与前一帧各自框内，框对齐近似）
                def mouth_roi(g, rr):
                    mx1 = int(rr[0] + 0.25 * rr[2]); mx2 = int(rr[0] + 0.75 * rr[2])
                    my1 = int(rr[1] + 0.55 * rr[3]); my2 = int(rr[1] + 0.95 * rr[3])
                    h_, w_ = g.shape
                    if mx2 <= mx1 or my2 <= my1 or mx1 < 0 or my1 < 0 or mx2 > w_ or my2 > h_:
                        return None
                    return g[my1:my2, mx1:mx2]
                roi0 = mouth_roi(prev_gray, prev_rect)
                roi1 = mouth_roi(gray, rect)
                if roi0 is not None and roi1 is not None:
                    r0 = cv2.resize(roi0, (64, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
                    r1 = cv2.resize(roi1, (64, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
                    mouth_ts.append(ts)
                    mouth_motion.append(float(np.abs(r1 - r0).mean()))
            prev_gray, prev_rect = gray, rect
    finally:
        cap.release()

    if len(mouth_motion) < 10:
        return {}

    # ---- 交叉相关（z-score 归一化，滞后 ±0.3s） ----
    mt = np.array(mouth_ts)
    mm = np.array(mouth_motion)
    mm = (mm - mm.mean()) / (mm.std() + 1e-9)
    env_at_mt = np.interp(mt, audio_ts, audio_env)
    env_at_mt = (env_at_mt - env_at_mt.mean()) / (env_at_mt.std() + 1e-9)

    best_corr, best_lag = -1.0, 0.0
    for lag in range(-LIP_LAG_SAMPLES, LIP_LAG_SAMPLES + 1):
        if lag == 0:
            a, b = env_at_mt, mm
        elif lag < 0:
            a, b = env_at_mt[-lag:], mm[:lag]
        else:
            a, b = env_at_mt[:-lag], mm[lag:]
        if len(a) < 10:
            continue
        c = float(np.corrcoef(a, b)[0, 1])
        if c > best_corr:
            best_corr, best_lag = c, lag * LIP_SAMPLE_INTERVAL
    if best_corr < 0:
        return {}
    return {'lip_sync_corr': round(best_corr, 3),
            'lip_sync_lag': round(best_lag, 2)}


# ==================================================================
# 控方证据子分（模型逐项证据挖掘，v5.5）
# ------------------------------------------------------------------
# 模型整体票是噪声（AUC≈0.53），但其控方轮输出的逐项证据表中，
# 7 个分离性单项的"异常"计数有判别力：48段校准样本中
# CV漏检伪造 24/26 子分≥3，低先验真实 2/10 子分≥3（中位 6 vs 0）。
# 分离性单项：#2 面部拉伸、#4 肤色帧间波动、#7 毛发边缘、#10 微表情、
# #11 帧间突变、#12 颈部色差、#13 耳朵扭曲。
# ==================================================================

PROSECUTOR_EVIDENCE_ITEMS = ('2', '4', '7', '10', '11', '12', '13')


def prosecutor_evidence_score(content: str) -> int:
    """从控方轮输出的逐项判定表提取证据子分（分离性单项的"异常"计数）。"""
    out = set()
    in_table = False
    for line in (content or '').splitlines():
        s = line.strip()
        if s.startswith('| # |') or s.startswith('|---'):
            in_table = True
            continue
        if in_table and s.startswith('|'):
            cols = [c.strip() for c in s.split('|')]
            if len(cols) >= 4 and cols[1].isdigit():
                rating = cols[3].strip().strip('*').strip()
                if rating == '异常':
                    out.add(cols[1])
            elif cols and cols[1] and not cols[1].isdigit():
                break
    return len(out & set(PROSECUTOR_EVIDENCE_ITEMS))


# ==================================================================
# 物理证据子分（守卫规则用）
# ------------------------------------------------------------------
# 物理一致性特征（遮挡/转动类）对应"真实拍摄无法产生的伪影"，特异性最高。
# 时长等风格特征被剔除后，回归先验可能低估此类伪造（如 F97/F99），
# 用物理特征子分单独兜底：子分超过阈值时，即使先验不足也强制至少"存疑"。
# ==================================================================

PHYS_GUARD_FEATURES = (
    'occl_edge_ratio', 'occl_edge_ratio_min',
    'face_box_jitter', 'face_size_jitter',
)


def physical_evidence_score(result: dict, model: dict | None = None) -> float | None:
    """物理特征加权 z 子分之和。model 缺省用新先验模型；特征缺失返回 None。"""
    if model is None:
        model = _load_model(_PRIOR_MODEL_PATH)
    if model is None:
        return None
    raw = {
        'occl_edge_ratio': float(result.get('occl_edge_ratio', 0.0) or 0.0),
        'occl_edge_ratio_min': float(result.get('occl_edge_ratio_min', 0.0) or 0.0),
        'face_box_jitter': float(result.get('face_box_jitter', 0.0) or 0.0),
        'face_size_jitter': float(result.get('face_size_jitter', 0.0) or 0.0),
    }
    if not any(result.get(k) is not None for k in raw):
        return None
    score = 0.0
    found = False
    for name, mu, sd, w in zip(model['features'], model['mu'], model['sd'], model['weights']):
        if name not in raw:
            continue
        found = True
        sd = sd if sd > 1e-9 else 1.0
        score += w * (raw[name] - mu) / sd
    if not found:
        return None
    return float(max(-PHYS_SCORE_CLIP, min(PHYS_SCORE_CLIP, score)))


def compute_prior(result: dict, p_override: float | None = None) -> str | None:
    """
    返回中性先验文本（注入提示词供交叉参考）。模型不存在时返回 None。
    p_override 传入稳定先验值时优先使用（与路由/终裁保持一致）。
    """
    p = p_override if p_override is not None else compute_prior_probability(result)
    if p is None:
        return None
    if p >= 0.7:
        level = "偏高"
    elif p >= 0.4:
        level = "中等"
    else:
        level = "偏低"
    return (
        f"\n\n【预处理先验】该视频的量化特征与已标注伪造视频集的相似度 P={p:.0%}"
        f"（先验水平：{level}）。该值仅来自传统 CV 特征，与真实结论可能不一致，仅供交叉参考。"
    )


# ==================================================================
# 稳定先验：跨阶段缓存 + 多次计算取中位数
# （视频解码存在非确定性，单次先验波动可达±0.2，直接拖累路由与终裁）
# ==================================================================

_prior_cache: dict = {}


def _file_signature(path: str) -> tuple | None:
    try:
        st = os.stat(path)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def stable_prior_probability(video_path: str, first_result: dict | None = None,
                             n_runs: int = 3, fusion: str = 'max') -> float | None:
    """
    计算稳定的 P(伪造|预处理特征)：
    1. 进程内缓存（按文件签名）：阶段一算一次，阶段二直接复用，保证路由一致性
    2. 缓存未命中时多次计算取中位数，消除解码非确定性带来的波动
    3. 双先验融合（v5.2）：新模型（16特征，抓物理一致性伪影）+ 旧模型
       （v16，12特征）按 fusion 规则合并（max=取高值，mean=取均值）。
       200视频校准：max@0.55 → 检出100%/误报14%；new@0.55 → 89%/7%
    """
    cache_key = (video_path, fusion)
    sig = _file_signature(video_path)
    if sig is not None:
        hit = _prior_cache.get(cache_key)
        if hit and hit[0] == sig:
            return hit[1]

    results = []
    if first_result is not None and 'error' not in first_result:
        results.append(first_result)
    for _ in range(n_runs - len(results)):
        r = analyze_video(video_path)
        if 'error' not in r:
            results.append(r)

    new_model = _load_model(_PRIOR_MODEL_PATH)
    v16_model = _load_model(_PRIOR_V16_PATH)

    def fused(r: dict) -> float | None:
        vals = []
        if new_model is not None:
            p = _prior_with_model(r, new_model)
            if p is not None:
                vals.append(p)
        if v16_model is not None:
            p = _prior_with_model(r, v16_model)
            if p is not None:
                vals.append(p)
        if not vals:
            return None
        if fusion == 'mean':
            return float(sum(vals) / len(vals))
        return float(max(vals))  # 默认 max：任一模型认为可疑即取高值

    priors = [p for p in (fused(r) for r in results) if p is not None]
    if not priors:
        return None
    med = float(sorted(priors)[len(priors) // 2])
    if sig is not None:
        _prior_cache[cache_key] = (sig, med)
    return med


# ==================================================================
# 事件帧提取（送检层证据图）
# ------------------------------------------------------------------
# 视觉模型对视频的理解存在内部稀疏抽帧与分辨率降级，转动伪影（帧间抖动）
# 与遮挡破坏（像素级交界涂抹）在整帧送审时不可见。本模块提取三类证据图，
# 作为补充图像与视频一起送检：
#   1. 遮挡交界放大图：人脸内部强边缘密度最高的帧 → 人脸区域裁剪放大
#      （文字笔画/话筒杆等外来物穿越人脸时边缘密度显著升高）
#   2. 转动序列对比图：正脸检测"存在→消失→再现"（Haar 只检正脸，侧脸漏检）
#      片段的连续帧并排拼接，供模型跨帧对比五官位置的连续性
#   3. 帧差增强图：相邻帧差异放大 6 倍，帧率级抖动/闪烁表现为杂乱高亮
# ==================================================================

EVENT_SAMPLE_INTERVAL = 0.4        # 事件扫描采样间隔（秒）
EVENT_MAX_FRAMES = 60              # 事件扫描帧数上限
EVENT_EDGE_THRESHOLD = 90          # Sobel 强边缘判定阈值
EVENT_DIFF_GAIN = 6.0              # 帧差放大倍数
CROP_PAD = 1.6                     # 人脸裁剪外扩系数
CROP_MAX_DIM = 1024                # 裁剪图最长边
STRIP_MAX_DIM = 640                # 序列拼接单帧最长边
EVENT_START_SKIP = 0.3             # 跳过开头秒数（避免黑场/转场干扰）


def _crop_face_region(frame: np.ndarray, rect: tuple,
                      pad: float = CROP_PAD, max_dim: int = CROP_MAX_DIM) -> np.ndarray | None:
    """按人脸框外扩裁剪并缩放至最长边 ≤ max_dim。"""
    h, w = frame.shape[:2]
    x, y, fw, fh = rect
    cx, cy = x + fw / 2.0, y + fh / 2.0
    side = max(fw, fh) * pad
    x1, y1 = max(0, int(cx - side / 2)), max(0, int(cy - side / 2))
    x2, y2 = min(w, int(cx + side / 2)), min(h, int(cy + side / 2))
    if x2 <= x1 or y2 <= y1:
        return None
    roi = frame[y1:y2, x1:x2]
    scale = max_dim / max(roi.shape[:2])
    if scale < 1.0:
        roi = cv2.resize(roi, (int(roi.shape[1] * scale), int(roi.shape[0] * scale)),
                         interpolation=cv2.INTER_AREA)
    return roi


def extract_event_frames(video_path: str, max_images: int = 4) -> list[dict]:
    """
    提取三类补充证据图。返回 [{"label": str, "ts": float, "image": BGR ndarray}]
    顺序：遮挡交界放大图 → 转动序列对比图 → 帧差增强图（共 ≤ max_images 张）。
    无有效人脸或视频无法打开时返回空列表。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning("事件帧提取：无法打开视频 %s", video_path)
        return []

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0
        duration = total_frames / fps
        if duration <= 0:
            return []

        start = EVENT_START_SKIP
        end = max(start + 0.5, duration - 0.3)
        n = min(EVENT_MAX_FRAMES, max(3, math.ceil((end - start) / EVENT_SAMPLE_INTERVAL)))
        timestamps = list(np.linspace(start, end, n))

        # ---- 密集扫描：人脸框 / 人脸内强边缘密度 / 相邻帧差异 ----
        frames, rects, edge_density, diffs = [], [], [], []
        prev_gray = None
        for ts in timestamps:
            got = _read_frame_at(cap, ts)
            if got is None:
                frames.append(None)
                rects.append(None)
                edge_density.append(0.0)
                diffs.append(0.0)
                prev_gray = None
                continue
            _, frame = got
            rect = _detect_face(frame) or _detect_face_relaxed(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            dens = 0.0
            if rect is not None:
                x, y, fw, fh = rect
                # 人脸框内部中心 60% 区域（避开轮廓与发际线边缘）
                ix1, iy1 = x + int(fw * 0.2), y + int(fh * 0.2)
                ix2, iy2 = x + int(fw * 0.8), y + int(fh * 0.8)
                if ix2 > ix1 and iy2 > iy1:
                    inner = gray[iy1:iy2, ix1:ix2]
                    mag = cv2.Sobel(inner, cv2.CV_32F, 1, 1, ksize=3)
                    dens = float(np.mean(np.abs(mag) > EVENT_EDGE_THRESHOLD))

            diff = 0.0
            if prev_gray is not None:
                if rect is not None:
                    x, y, fw, fh = rect
                    diff = float(np.mean(cv2.absdiff(gray[y:y + fh, x:x + fw],
                                                    prev_gray[y:y + fh, x:x + fw])))
                else:
                    diff = float(np.mean(cv2.absdiff(gray, prev_gray)))
            prev_gray = gray
            frames.append(frame)
            rects.append(rect)
            edge_density.append(dens)
            diffs.append(diff)

        valid = [i for i in range(len(frames)) if frames[i] is not None]
        if not valid:
            return []

        # ---- 转动事件：正脸检测"存在→消失→再现"片段 ----
        rot_seg = None
        for i in range(1, len(rects)):
            if rects[i] is None and rects[i - 1] is not None:
                j = i
                while j < len(rects) and rects[j] is None:
                    j += 1
                if j < len(rects) and rects[j] is not None:  # 正脸再现
                    rot_seg = (i - 1, j)
                    break
                # 未再现则继续向后扫描（视频结尾丢失正脸属正常）

        out = []

        # 1) 遮挡交界放大图：人脸内强边缘密度最高的帧
        cand = [i for i in valid if rects[i] is not None]
        if cand:
            occ_i = max(cand, key=lambda i: edge_density[i])
            crop = _crop_face_region(frames[occ_i], rects[occ_i])
            if crop is not None:
                ts = timestamps[occ_i]
                cv2.putText(crop, f"t={ts:.1f}s", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                out.append({"label": "遮挡交界放大图（人脸内强边缘密度最高帧）",
                            "ts": ts, "image": crop})

        # 2) 转动序列对比图：缺席段两端各取 2 帧，按同一人脸框裁剪并排
        if rot_seg is not None:
            a, b = rot_seg
            ref_rect = rects[a]
            idxs = sorted(set([a, a + 1, b - 1, b]))
            idxs = [i for i in idxs if 0 <= i < len(frames) and frames[i] is not None]
            if len(idxs) >= 3 and ref_rect is not None:
                cells = []
                for i in idxs:
                    cell = _crop_face_region(frames[i], ref_rect, pad=CROP_PAD,
                                             max_dim=STRIP_MAX_DIM)
                    if cell is None:  # 裁剪失败则整帧缩放进拼接
                        s = STRIP_MAX_DIM / max(frames[i].shape[:2])
                        if s < 1.0:
                            cell = cv2.resize(frames[i],
                                              (int(frames[i].shape[1] * s), int(frames[i].shape[0] * s)),
                                              interpolation=cv2.INTER_AREA)
                        else:
                            cell = frames[i]
                    cv2.putText(cell, f"t={timestamps[i]:.1f}s", (8, 26),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cells.append(cell)
                h = max(c.shape[0] for c in cells)
                cells = [cv2.copyMakeBorder(c, 0, h - c.shape[0], 0, 0,
                                            cv2.BORDER_CONSTANT, value=(255, 255, 255))
                         for c in cells]
                sep = np.full((h, 8, 3), 255, np.uint8)
                strip = cells[0]
                for c in cells[1:]:
                    strip = np.hstack([strip, sep, c])
                out.append({"label": "转动序列对比图（正脸消失→再现片段，跨帧对比五官连续性）",
                            "ts": timestamps[a], "image": strip})

        # 3) 帧差增强图：帧差最大的 2 处（转动事件存在时优先取事件段内）
        diff_cands = [i for i in valid if diffs[i] > 0]
        if rot_seg is not None:
            a, b = rot_seg
            in_seg = [i for i in diff_cands if a - 1 <= i <= b]
            if in_seg:
                diff_cands = in_seg
        for di in sorted(diff_cands, key=lambda i: -diffs[i])[:2]:
            if len(out) >= max_images:
                break
            prev = di - 1
            if frames[prev] is None:
                continue
            g0 = cv2.cvtColor(frames[prev], cv2.COLOR_BGR2GRAY)
            g1 = cv2.cvtColor(frames[di], cv2.COLOR_BGR2GRAY)
            dmap = cv2.absdiff(g0, g1).astype(np.float32) * EVENT_DIFF_GAIN
            dmap = np.clip(dmap, 0, 255).astype(np.uint8)
            dmap = cv2.applyColorMap(dmap, cv2.COLORMAP_TURBO)
            rect = rects[di] if rects[di] is not None else rects[prev]
            if rect is not None:
                dmap = _crop_face_region(dmap, rect)
            cv2.putText(dmap, f"diff t={timestamps[di]:.1f}s x{EVENT_DIFF_GAIN:.0f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            out.append({"label": "帧差增强图（相邻帧差异放大，抖动/闪烁表现为杂乱高亮）",
                        "ts": timestamps[di], "image": dmap})

        logger.debug("  [事件帧] %s: 提取 %d 张证据图",
                     Path(video_path).name, len(out))
        return out[:max_images]
    finally:
        cap.release()


# ==================================================================
# 先验表值查询（v5.7 锚定用）
# ==================================================================

_table_prior_cache: dict = {}


def table_prior_value(video_path: str) -> float | None:
    """从稳定先验表查询表值（按文件名匹配，带缓存）。表缺失返回None。"""
    import csv
    global _table_prior_cache
    if not _table_prior_cache:
        try:
            p = Path(__file__).resolve().parent.parent / 'output' / 'stable_prior_table.csv'
            with open(p, encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    _table_prior_cache[row['video'].rsplit('.', 1)[0]] = float(row['prior'])
        except Exception:
            return None
    name = Path(video_path).stem
    return _table_prior_cache.get(name)


# ==================================================================
# CV 证据图（v5.6：纹理密度热力图 + 面颈清晰度剖面）
# ------------------------------------------------------------------
# 配对实验（阶段E）证明：模型无法自行发现/核验"面部软化"指纹，
# 但将 CV 测量结果可视化后注入（热力图+剖面曲线），模型能在部分
# 假脸上"看图读结论"（敏感~45%/特异~93%，两轮复现）。机理：
# 注意力锚定 + 视觉模式启动。
# ==================================================================


def extract_cv_evidence(video_path: str) -> list[dict]:
    """生成两张 CV 证据图：纹理密度热力图、面颈清晰度剖面曲线。"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        dur = total / fps
        best = None
        for f in (0.3, 0.5, 0.7):
            got = _read_frame_at(cap, dur * f)
            if got is None:
                continue
            _, fr = got
            r = _detect_face(fr)
            if r is not None:
                area = r[2] * r[3]
                if best is None or area > best[0]:
                    best = (area, fr, r)
    finally:
        cap.release()
    if best is None:
        return []
    _, frame, (x, y, fw, fh) = best
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lap2 = cv2.Laplacian(gray, cv2.CV_32F) ** 2

    # 1) 纹理密度热力图（24px 块内拉普拉斯方差）
    bs = 24
    hh, ww = h // bs + 1, w // bs + 1
    heat = np.zeros((hh, ww), np.float32)
    for i in range(0, h - bs, bs):
        for j in range(0, w - bs, bs):
            heat[i // bs, j // bs] = float(lap2[i:i + bs, j:j + bs].mean())
    heat = np.sqrt(heat)
    heat = cv2.resize(heat, (w, h), interpolation=cv2.INTER_CUBIC)
    hn = (heat - heat.min()) / (heat.max() - heat.min() + 1e-9)
    heat_c = cv2.applyColorMap((hn * 255).astype(np.uint8), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(frame, 0.55, heat_c, 0.45, 0)
    cv2.rectangle(overlay, (x, y), (x + fw, y + fh), (0, 255, 0), 4)
    ny1 = y + fh + int(fh * 0.05)
    ny2 = min(h, y + fh + int(fh * 0.9))
    if ny2 > ny1:
        cv2.rectangle(overlay, (x + int(fw * 0.2), ny1), (x + int(fw * 0.8), ny2), (0, 0, 255), 4)
    cv2.putText(overlay, 'GREEN=face RED=neck warm=texture cool=smooth', (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    # 2) 面颈清晰度剖面（沿面部中心竖线）
    cx = x + fw // 2
    y_top = max(0, y - int(fh * 0.2))
    y_bot = min(h, y + fh + int(fh * 0.9))
    band = lap2[y_top:y_bot, max(0, cx - 15):min(w, cx + 15)]
    prof = np.sqrt(band.mean(axis=1))
    prof = np.convolve(prof, np.ones(15) / 15, mode='same')
    W2, H2 = 960, 540
    canvas = np.full((H2, W2, 3), 255, np.uint8)
    xs = np.linspace(0, W2 - 1, len(prof))
    ys = H2 - 40 - (prof / (prof.max() + 1e-9)) * (H2 - 100)
    cv2.polylines(canvas, [np.stack([xs, ys], axis=1).astype(np.int32)], False, (0, 0, 255), 3)
    fb_x = int((y + fh - y_top) / max(1, (y_bot - y_top)) * (W2 - 1))
    cv2.line(canvas, (fb_x, 0), (fb_x, H2), (0, 180, 0), 2)
    cv2.putText(canvas, 'FACE', (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 150, 0), 3)
    cv2.putText(canvas, 'NECK', (fb_x + 30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 200), 3)
    cv2.putText(canvas, 'x=top-to-bottom sharpness  green line=face/neck boundary',
                (20, H2 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 80, 80), 2)
    return [
        {'label': 'CV证据图1：纹理密度热力图（绿框=人脸/红框=颈部，暖色=纹理细节多/冷色=平滑）',
         'ts': 0.0, 'image': overlay},
        {'label': 'CV证据图2：面颈清晰度剖面（绿线=面颈分界，左面部/右颈部，纵轴=纹理细节强度）',
         'ts': 0.0, 'image': canvas},
    ]


# ==================================================================
# 物理一致性定量特征（密集扫描）
# ------------------------------------------------------------------
# VL 模型对低分辨率像素级伪影（遮挡破坏/转动抖动）不可见，只能靠 CV 在
# 像素层面直接量化。四类特征（与事件帧提取共用采样参数）：
#   occl_edge_ratio     遮挡边缘衰减：高边缘密度帧中，人脸内强边缘梯度中位数
#                       / 人脸外强边缘梯度中位数。换脸重绘涂抹人脸内的
#                       遮挡物边缘 → 比值下降
#   occl_edge_ratio_min 上述比值的最小值（最严重涂抹帧）
#   edge_persist_ratio  边缘时序持续率：人脸内（按框对齐）强边缘逐帧重合率
#                       / 人脸外强边缘逐帧重合率。换脸逐帧重渲染使
#                       人脸内边缘不稳定 → 比值下降
#   face_box_jitter     人脸框中心位移 MAD（按框宽归一）——转动抖动
#   face_size_jitter    人脸框宽变化 MAD（按框宽归一）
# ==================================================================

PHYS_EDGE_DENSITY_MIN = 0.02   # 人脸内强边缘密度下限（低于此值不计算遮挡边缘比）
PHYS_INNER_MIN_PX = 50         # 人脸内强边缘像素数下限
PHYS_EDGE_THRESHOLD = EVENT_EDGE_THRESHOLD
PHYS_ALIGN_SIZE = 96           # 框对齐边缘重合率计算的归一化尺寸


def _crop_inner(frame: np.ndarray, rect: tuple, size: int = PHYS_ALIGN_SIZE) -> np.ndarray | None:
    """裁剪人脸内中心 60% 区域并归一化到 size×size（框对齐用）。"""
    x, y, fw, fh = rect
    ix1, iy1 = x + int(fw * 0.2), y + int(fh * 0.2)
    ix2, iy2 = x + int(fw * 0.8), y + int(fh * 0.8)
    if ix2 <= ix1 or iy2 <= iy1:
        return None
    return cv2.resize(frame[iy1:iy2, ix1:ix2], (size, size), interpolation=cv2.INTER_AREA)


def _outer_ring_mask(edge_mask: np.ndarray, rect: tuple) -> np.ndarray | None:
    """人脸外环带强边缘掩码（人脸框外扩一倍并挖掉人脸框本身）。"""
    h, w = edge_mask.shape
    x, y, fw, fh = rect
    ox1, ox2 = max(0, x - fw), min(w, x + 2 * fw)
    oy1, oy2 = max(0, y - fh), min(h, y + 2 * fh)
    outer = edge_mask[oy1:oy2, ox1:ox2].copy()
    fy1 = max(0, y) - oy1
    fy2 = min(h, y + fh) - oy1
    fx1 = max(0, x) - ox1
    fx2 = min(w, x + fw) - ox1
    if not (0 <= fy1 < fy2 and 0 <= fx1 < fx2):
        return None
    outer[fy1:fy2, fx1:fx2] = False
    return outer


def _dense_physical_scan(video_path: str) -> dict:
    """
    密集扫描视频，量化物理一致性特征。返回特征 dict（可能为空）。
    与 extract_event_frames 的扫描逻辑同构，但输出数值特征而非图像。
    特征（全部为内容特征，不含时长等元数据）：
      遮挡/转动类：occl_edge_ratio(_min)、face_box_jitter、face_size_jitter
      内容指纹类（v5.3 新增，补偿时长特征剔除后的信号损失）：
        noise_ratio     人脸内噪声残留 std / 人脸外环带噪声残留 std
        chroma_diff     人脸内与背景的 Lab 色度距离
        rot_diff_energy 转动/最大运动段的人脸区帧差能量 / 全局帧差能量
        flow_consistency 人脸区光流幅值 / 全局光流幅值（运动段）
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {}
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0
        duration = total_frames / fps
        if duration <= 0:
            return {}

        start = EVENT_START_SKIP
        end = max(start + 0.5, duration - 0.3)
        n = min(EVENT_MAX_FRAMES, max(3, math.ceil((end - start) / EVENT_SAMPLE_INTERVAL)))
        timestamps = list(np.linspace(start, end, n))

        occ_ratios = []       # 高边缘密度帧：人脸内/外强边缘梯度比
        centers_px = []       # 人脸框中心 (px)
        widths = []           # 人脸框宽 (px)
        rects = []            # 逐帧人脸框（转动事件检测用）
        noise_ratios = []     # 人脸内/外噪声残留比
        chroma_diffs = []     # 人脸-背景色度距离
        pair_face_diff = []   # (帧序号, 人脸区帧差, 全局帧差)
        flow_candidates = []  # 帧差最大的前2对 (diff_face, g0, g1, rect)

        prev_gray = None
        prev_rect = None
        flow_scale = 0.5      # 光流计算缩放（最长边320px）

        for i, ts in enumerate(timestamps):
            got = _read_frame_at(cap, ts)
            if got is None:
                prev_gray = prev_rect = None
                continue
            _, frame = got
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rect = _detect_face(frame) or _detect_face_relaxed(frame)
            mag = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 1, ksize=3))
            edge_mask = mag > PHYS_EDGE_THRESHOLD
            rects.append(rect)

            if rect is not None:
                x, y, fw, fh = rect
                centers_px.append((x + fw / 2.0, y + fh / 2.0))
                widths.append(float(fw))

                # 1) 遮挡边缘衰减：人脸内中心 60% 区域 vs 人脸外环带
                inner_crop = _crop_inner(gray, rect)
                inner_mag = _crop_inner(mag, rect)
                if inner_crop is not None:
                    inner_mask = inner_mag > PHYS_EDGE_THRESHOLD
                    if inner_mask.sum() > PHYS_INNER_MIN_PX:
                        m_in = float(np.median(inner_mag[inner_mask]))
                        outer = _outer_ring_mask(edge_mask, rect)
                        if outer is not None and np.any(outer):
                            m_out = float(np.median(_outer_region_slice(mag, rect, outer)))
                            if m_out > 0:
                                occ_ratios.append(m_in / m_out)

                # 2) 噪声残留比（高斯平滑残差的 std）：人脸内 vs 外环带
                noise = (gray.astype(np.float32)
                         - cv2.GaussianBlur(gray, (3, 3), 0).astype(np.float32))
                n_in = float(noise[y:y + fh, x:x + fw].std())
                n_out_region, _ = _outer_ring_region(noise, rect)
                if n_out_region is not None and n_out_region.size > 0:
                    n_out = float(n_out_region.std())
                    if n_out > 0.5:
                        noise_ratios.append(n_in / n_out)

                # 3) 色度差：人脸内 Lab 色度均值 vs 背景四角
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                face_lab = lab[y:y + fh, x:x + fw].reshape(-1, 3).astype(np.float32)
                fa, fb = face_lab[:, 1].mean(), face_lab[:, 2].mean()
                bg = _corner_lab_mean(lab, rect)
                if bg is not None:
                    chroma_diffs.append(float(np.hypot(fa - bg[0], fb - bg[1])))

            # 4) 帧差（人脸区 / 全局）与光流候选
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray).astype(np.float32)
                d_global = float(diff.mean())
                d_face = d_global
                r_now = rect if rect is not None else prev_rect
                if r_now is not None:
                    fx, fy, fw2, fh2 = r_now
                    d_face = float(diff[fy:fy + fh2, fx:fx + fw2].mean())
                pair_face_diff.append((i, d_face, d_global))
                # 帧差大 → 光流候选（只保留前 2 对）
                if d_face > 3.0:
                    cand = (d_face, prev_gray.copy(), gray.copy(), r_now)
                    if len(flow_candidates) < 2:
                        flow_candidates.append(cand)
                    elif d_face > flow_candidates[0][0] or d_face > flow_candidates[1][0]:
                        flow_candidates.sort(key=lambda t: t[0])
                        flow_candidates[0] = cand
            prev_gray = gray
            prev_rect = rect

        out = {}
        if occ_ratios:
            out['occl_edge_ratio'] = round(float(np.mean(occ_ratios)), 3)
            out['occl_edge_ratio_min'] = round(float(np.min(occ_ratios)), 3)
        if len(centers_px) >= 3:
            c = np.array(centers_px, dtype=float)
            wdt = np.array(widths, dtype=float)
            rel_disp = np.sqrt(((np.diff(c, axis=0)) ** 2).sum(axis=1)) \
                / np.maximum((wdt[1:] + wdt[:-1]) / 2.0, 1.0)
            size_chg = np.abs(np.diff(wdt)) / np.maximum(wdt[:-1], 1.0)
            out['face_box_jitter'] = round(
                float(np.median(np.abs(rel_disp - np.median(rel_disp)))), 4)
            out['face_size_jitter'] = round(
                float(np.median(np.abs(size_chg - np.median(size_chg)))), 4)
        if noise_ratios:
            out['noise_ratio'] = round(float(np.mean(noise_ratios)), 3)
        if chroma_diffs:
            out['chroma_diff'] = round(float(np.mean(chroma_diffs)), 3)

        # 转动事件段（正脸消失→再现）内的帧差能量比；无事件则取帧差最大 2 对
        rot_seg = None
        for i in range(1, len(rects)):
            if rects[i] is None and rects[i - 1] is not None:
                j = i
                while j < len(rects) and rects[j] is None:
                    j += 1
                if j < len(rects) and rects[j] is not None:
                    rot_seg = (i - 1, j)
                    break
        energy_pairs = pair_face_diff
        if rot_seg is not None:
            a, b = rot_seg
            in_seg = [p for p in pair_face_diff if a - 1 <= p[0] <= b]
            if in_seg:
                energy_pairs = in_seg
        if energy_pairs:
            vals = [df / max(dg, 1e-6) for _, df, dg in energy_pairs]
            out['rot_diff_energy'] = round(float(np.mean(vals)), 3)

        # 光流一致性：人脸区光流幅值 / 全局（帧差最大的运动段）
        flow_ratios = []
        for _, g0, g1, r_now in sorted(flow_candidates, key=lambda t: -t[0]):
            if r_now is None:
                continue
            s = flow_scale * 320.0 / max(g0.shape)
            g0s = cv2.resize(g0, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            g1s = cv2.resize(g1, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            fl = cv2.calcOpticalFlowFarneback(g0s, g1s, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            fmag = np.sqrt((fl ** 2).sum(axis=2))
            fx, fy, fw2, fh2 = r_now
            fx1, fy1 = int(fx * s), int(fy * s)
            fx2, fy2 = int((fx + fw2) * s), int((fy + fh2) * s)
            fx1, fy1 = max(0, fx1), max(0, fy1)
            fx2, fy2 = min(fmag.shape[1], fx2), min(fmag.shape[0], fy2)
            if fx2 > fx1 and fy2 > fy1:
                f_face = float(fmag[fy1:fy2, fx1:fx2].mean())
                f_glob = float(fmag.mean()) + 1e-6
                flow_ratios.append(f_face / f_glob)
        if flow_ratios:
            out['flow_consistency'] = round(float(np.mean(flow_ratios)), 3)
        return out
    finally:
        cap.release()


def _outer_ring_region(arr: np.ndarray, rect: tuple) -> tuple[np.ndarray | None, bool]:
    """取人脸外环带区域（外扩一倍挖掉人脸框）。返回 (区域, 是否有效)。"""
    h, w = arr.shape
    x, y, fw, fh = rect
    ox1, ox2 = max(0, x - fw), min(w, x + 2 * fw)
    oy1, oy2 = max(0, y - fh), min(h, y + 2 * fh)
    region = arr[oy1:oy2, ox1:ox2].copy()
    fy1 = max(0, y) - oy1
    fy2 = min(h, y + fh) - oy1
    fx1 = max(0, x) - ox1
    fx2 = min(w, x + fw) - ox1
    if not (0 <= fy1 < fy2 and 0 <= fx1 < fx2):
        return None, False
    region[fy1:fy2, fx1:fx2] = np.nan
    region = region[~np.isnan(region)]
    return region, True


def _corner_lab_mean(lab: np.ndarray, rect: tuple) -> tuple | None:
    """背景四角的 Lab 色度均值 (a, b)（避开人脸框）。"""
    h, w = lab.shape[:2]
    x, y, fw, fh = rect
    corners = [
        (0, 0, w // 4, h // 4),
        (w - w // 4, 0, w // 4, h // 4),
        (0, h - h // 4, w // 4, h // 4),
        (w - w // 4, h - h // 4, w // 4, h // 4),
    ]
    vals = []
    for cx, cy, cw, ch in corners:
        if (cx < x + fw and cx + cw > x and cy < y + fh and cy + ch > y):
            continue
        blk = lab[cy:cy + ch, cx:cx + cw].reshape(-1, 3).astype(np.float32)
        vals.append((blk[:, 1].mean(), blk[:, 2].mean()))
    if not vals:
        return None
    return (float(np.mean([v[0] for v in vals])), float(np.mean([v[1] for v in vals])))


def _outer_region_slice(mag: np.ndarray, rect: tuple, outer_mask: np.ndarray) -> np.ndarray:
    """取 mag 中人脸外环带对应位置的像素值（与 _outer_ring_mask 同坐标）。"""
    h, w = mag.shape
    x, y, fw, fh = rect
    ox1, ox2 = max(0, x - fw), min(w, x + 2 * fw)
    oy1, oy2 = max(0, y - fh), min(h, y + 2 * fh)
    region = mag[oy1:oy2, ox1:ox2]
    return region[outer_mask]
