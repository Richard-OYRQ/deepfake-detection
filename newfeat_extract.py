# -*- coding: utf-8 -*-
"""第四信号特征提取：rPPG(PPG) + 频域(FFT) + 唇同步(lip-sync)。
对留出集 160 条逐条提取（纯 CV，无 API 调用），输出 output_newfeat_160.json。
帧环 10fps ≤200 帧，rPPG 与频域共享；唇同步复用 preprocessor._lip_sync_scan。"""
import glob
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, r"E:\deepfake\src")
from preprocessor import (_detect_face, _detect_face_relaxed, _read_frame_at,  # noqa: E402
                          _lip_sync_scan)

SRC = r"E:\deepfake\_self160"
SAMPLE_FPS = 10
MAX_FRAMES = 200
PPG_LO, PPG_HI = 0.75, 4.0          # 脉率带 Hz（45–240 bpm）
N_RBINS = 32                        # 方位角谱分箱数
N_CORNER_BINS = 8                   # 径向 >0.8 的角区（棋盘格伪影检测）


def _azimuthal_spectrum(gray: np.ndarray):
    """人脸区 2D FFT 的径向归一化方位角谱（32 箱）与角区能量比。"""
    g = gray.astype(np.float32)
    g -= g.mean()
    h, w = g.shape
    # 2 的幂裁剪加速 + 减少边缘效应
    s = 2 ** int(np.log2(min(h, w)))
    g = g[:s, :s]
    mag = np.abs(np.fft.fftshift(np.fft.fft2(g)))
    c = s // 2
    yidx, xidx = np.indices((s, s))
    rad = np.sqrt((yidx - c) ** 2 + (xidx - c) ** 2) / c
    az = np.zeros(N_RBINS)
    for k in range(N_RBINS):
        lo, hi = (k + 0.5) / N_RBINS, (k + 1.5) / N_RBINS
        m = (rad >= lo) & (rad < hi)
        az[k] = mag[m].mean() if m.any() else 0.0
    corner = mag[rad > 0.8].mean() / (mag.mean() + 1e-9)
    return az, corner


def extract(path: str) -> dict:
    feats = {}
    lip = _lip_sync_scan(path)
    feats["lip_corr"] = lip.get("lip_sync_corr")
    feats["lip_lag"] = lip.get("lip_sync_lag")
    feats["has_lip"] = bool(lip)

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return feats
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        n_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        dur = n_total / fps if fps > 0 else 0.0
        if dur <= 0.5:
            return feats
        t0 = min(0.3, dur * 0.05)
        t1 = max(t0 + 1.0, dur - 0.3)
        n_s = min(MAX_FRAMES, max(20, int((t1 - t0) * SAMPLE_FPS)))
        ts = np.linspace(t0, t1, n_s)

        green = []          # rPPG 原始信号（绿通道均值）
        az_specs = []       # 每帧方位角谱
        corners = []
        for t in ts:
            got = _read_frame_at(cap, t)
            if got is None:
                continue
            _, frame = got
            rect = _detect_face(frame) or _detect_face_relaxed(frame)
            if rect is None:
                continue
            x, y, w, h = rect
            roi = frame[y:y + h, x:x + w]
            if roi.size < 40 * 40:
                continue
            inner = roi[h // 5:4 * h // 5, w // 5:4 * w // 5]
            if inner.size >= 400:
                green.append(float(inner[..., 1].astype(np.float32).mean()))
            az, corner = _azimuthal_spectrum(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
            az_specs.append(az)
            corners.append(corner)
    finally:
        cap.release()

    # ---- rPPG：去趋势 + 脉率带 SNR ----
    feats["ppg_snr"] = feats["ppg_freq"] = feats["ppg_band"] = None
    if len(green) >= 30:
        sig = np.array(green, dtype=np.float64)
        sig -= np.convolve(sig, np.ones(10) / 10, mode="same")   # 1s 滑动均值去趋势
        sp = np.abs(np.fft.rfft(sig - sig.mean()))
        fr = np.fft.rfftfreq(len(sig), d=1.0 / SAMPLE_FPS)
        band = (fr >= PPG_LO) & (fr <= PPG_HI)
        if band.sum() >= 3:
            b = sp[band]
            feats["ppg_snr"] = float(b.max() / (np.median(b) + 1e-9))
            feats["ppg_freq"] = float(fr[band][np.argmax(b)])
            feats["ppg_band"] = float((b ** 2).sum() / ((sp ** 2).sum() + 1e-9))
    # ---- 频域 ----
    if az_specs:
        az = np.array(az_specs)
        az_mean = az.mean(axis=0)
        tot = az_mean.mean() + 1e-9
        feats["az_hf"] = float(az_mean[N_RBINS // 2:].mean() / tot)       # 高频能量比
        feats["az_peak"] = float(az_mean.max() / (np.median(az_mean) + 1e-9))  # 谱峰度
        feats["corner"] = float(np.mean(corners))                          # 棋盘格角能量
    return feats


def main():
    labels = {os.path.splitext(k)[0]: v for k, v in
              json.load(open(os.path.join(SRC, "labels.json"), encoding="utf-8")).items()}
    fusion = json.load(open(r"E:\deepfake\output_self160_fusion.json", encoding="utf-8"))
    rows = {r["name"]: r for r in fusion["rows"]}

    out_path = r"E:\deepfake\output_newfeat_160.json"
    done = {}
    if os.path.exists(out_path):
        done = {r["name"]: r for r in json.load(open(out_path, encoding="utf-8"))["rows"]}

    names = sorted(labels)
    t_start = time.time()
    for i, name in enumerate(names):
        if name in done:
            continue
        path = os.path.join(SRC, name + ".mp4")
        row = dict(rows.get(name, {}))
        row.update({"name": name, "label": labels[name]})
        row.update(extract(path))
        done[name] = row
        if (i + 1) % 10 == 0:
            el = time.time() - t_start
            out = {"rows": [done[n] for n in sorted(done)]}
            json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"[{i + 1}/{len(names)}] 已存 {out_path}（耗时 {el:.0f}s）", flush=True)
    out = {"rows": [done[n] for n in sorted(done)]}
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"全部完成: {len(done)} 条 → {out_path}", flush=True)


if __name__ == "__main__":
    main()
