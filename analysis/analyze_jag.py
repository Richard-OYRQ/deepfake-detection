# -*- coding: utf-8 -*-
"""锯齿伪影逐帧分析：
对 fake_e10_on_10 vs 10 逐帧（0.2s间隔）测量人脸左右边界与下颌线的
轮廓位置高频跳变（锯齿指纹=轮廓位置阶梯状跳变）。
规则候选：跳变率（大台阶帧占比）超过阈值 → 锯齿伪影信号。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'


def boundary_metrics(video_path, step=0.2):
    """逐帧返回 (时间戳, 左侧跳变率, 右侧跳变率, 下颌跳变率)。"""
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    rows = []
    ts = 0.1
    while ts < dur - 0.1:
        got = _read_frame_at(cap, ts)
        if got is not None:
            _, frame = got
            r = _detect_face(frame)
            if r is not None:
                m = frame_metrics(frame, r)
                if m is not None:
                    rows.append((round(ts, 1),) + m)
        ts += step
    cap.release()
    return rows


def frame_metrics(frame, rect):
    x, y, fw, fh = rect
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    y1 = y + int(fh * 0.15)
    y2 = y + int(fh * 0.75)
    if y2 - y1 < 30:
        return None

    def jitter_rate(band):
        """轮廓位置序列的大台阶跳变率。"""
        grad = np.abs(np.diff(band, axis=1))
        pos = np.argmax(grad, axis=1).astype(np.float32)
        steps = np.abs(np.diff(pos))
        if len(steps) < 10:
            return 0.0
        return float((steps >= 2).mean())  # ≥2px 跳变 = 台阶/锯齿

    rates = []
    for side in (-1, 1):
        bx = x + (fw if side > 0 else 0)
        x1 = max(0, bx - 20)
        x2 = min(w, bx + 20)
        if x2 - x1 < 20:
            continue
        band = gray[y1:y2, x1:x2]
        rates.append(jitter_rate(band))
    # 下颌线（横向扫描）
    yy1 = y + int(fh * 0.85)
    yy2 = min(h, y + fh + int(fh * 0.2))
    if yy2 - yy1 >= 20:
        x1 = max(0, x - int(fw * 0.15))
        x2 = min(w, x + fw + int(fw * 0.15))
        band = gray[yy1:yy2, x1:x2].T
        rates.append(jitter_rate(band))
    if not rates:
        return None
    return tuple(rates)


for tag, path in (('10(真)', os.path.join(BASE, 'videos', '10.mp4')),
                  ('e10(假)', os.path.join(BASE, 'pairset', 'outputs', 'fake_e10_on_10.mp4'))):
    rows = boundary_metrics(path)
    if not rows:
        print(tag, '无数据')
        continue
    arr = np.array([r[1:] for r in rows])
    print('===== %s：%d 帧 =====' % (tag, len(rows)))
    print('  跳变率(左/右/下颌) 均值: %.3f / %.3f / %.3f' % tuple(arr.mean(axis=0)))
    print('  跳变率最大值: %.3f / %.3f / %.3f' % tuple(arr.max(axis=0)))
    print('  每帧明细（前20帧）:')
    for r in rows[:20]:
        print('    t=%4.1fs  左=%.3f 右=%.3f 下颌=%.3f' % r)
    print()
