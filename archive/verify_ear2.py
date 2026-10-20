# -*- coding: utf-8 -*-
"""耳面结合部伪影测量 v2：
- 耳高度带：脸框 20%~60% 高度（耳朵所在纵向区间）
- 边界过渡宽度：脸框左右边界处的灰度跃迁跨度（像素数，模糊=更宽）
- 3帧平均 + 左右耳合并"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]


def transition_width(frame, rect, side):
    """边界过渡宽度：脸框侧边处的灰度跃迁跨度（模糊融合 → 跨度大）。"""
    x, y, fw, fh = rect
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    y1 = y + int(fh * 0.20)
    y2 = y + int(fh * 0.60)
    if y2 <= y1:
        return None
    bx = x + (fw if side > 0 else 0)
    if bx < 20 or bx > w - 20:
        return None
    # 该高度带内、沿边界取灰度剖面（多行平均）
    band = gray[y1:y2, bx - 20:bx + 20]
    prof = band.mean(axis=0)
    # 跃迁跨度 = 梯度绝对值最大点两侧的 10%-90% 上升区间宽度
    grad = np.abs(np.diff(prof))
    peak = int(np.argmax(grad))
    p10 = prof[peak] + 0.1 * (prof[-1] - prof[0])
    p90 = prof[peak] + 0.9 * (prof[-1] - prof[0])
    # 在峰值附近找跨越 p10/p90 的位置
    lo = hi = None
    for i in range(peak, 0, -1):
        if prof[i] <= p10:
            lo = i
            break
    for i in range(peak, len(prof)):
        if prof[i] >= p90:
            hi = i
            break
    if lo is None or hi is None:
        return None
    return float(hi - lo)


def measure(video_path):
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    vals = []
    for f in (0.3, 0.5, 0.7):
        got = _read_frame_at(cap, dur * f)
        if got is None:
            continue
        _, fr = got
        r = _detect_face(fr)
        if r is None:
            continue
        for side in (-1, 1):
            tw = transition_width(fr, r, side)
            if tw is not None:
                vals.append(tw)
    cap.release()
    return float(np.median(vals)) if vals else None


print(f'{"对":>4s} {"真·边界宽度":>12s} {"假·边界宽度":>12s} {"假更宽?":>8s}')
diffs = []
for n in NUMS:
    tr = measure(os.path.join(BASE, 'videos', '%d.mp4' % n))
    tf = measure(os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))
    if tr is None or tf is None:
        print(n, '数据不足')
        continue
    d = tf - tr
    diffs.append(d)
    print(f'{n:>4d} {tr:>12.1f} {tf:>12.1f} {"是" if d > 0 else "否":>8s}')

print()
print(f'假-真宽度差 均值={np.mean(diffs):+.1f}px | 假更宽的对数: {sum(1 for d in diffs if d > 0)}/{len(diffs)}')
