# -*- coding: utf-8 -*-
"""验证 16 个正式输出的换脸情况。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 22]
PAIR = r'D:\deepfake\pairset'


def check_one(n):
    out = os.path.join(PAIR, 'outputs', 'fake_e%d_on_%d.mp4' % (n, n))
    ori = os.path.join(r'D:\deepfake\videos', '%d.mp4' % n)
    cap_o = cv2.VideoCapture(out)
    cap_r = cv2.VideoCapture(ori)
    vals = []
    for ts in (0.5, 1.5, 3.0, 4.5, 6.0, 8.0, 10.0, 12.0, 14.0):
        go = _read_frame_at(cap_o, ts)
        gr = _read_frame_at(cap_r, ts)
        if go is None or gr is None:
            continue
        _, fo = go
        _, fr = gr
        r = _detect_face(fr)
        if r is None:
            continue
        x, y, fw, fh = r
        d_face = float(np.abs(fo[y:y + fh, x:x + fw].astype(np.float32)
                              - fr[y:y + fh, x:x + fw].astype(np.float32)).mean())
        d_bg = float(np.abs(fo[20:220,20:220].astype(np.float32) - fr[20:220,20:220].astype(np.float32)).mean())
        vals.append(d_face / max(d_bg, 1e-6))
    cap_o.release()
    cap_r.release()
    return vals


good, weak = [], []
print(f'{"编号":>4s} {"差比中位":>8s} {"换脸帧占比":>10s} {"判定":>6s}')
for n in NUMS:
    vals = check_one(n)
    if not vals:
        print(f'{n:>4d}  无数据')
        weak.append(n)
        continue
    med = np.median(vals)
    frac = sum(1 for v in vals if v > 2.5) / len(vals)
    v = '有效' if frac >= 0.5 else '弱' if frac >= 0.2 else '无效'
    print(f'{n:>4d} {med:>8.1f} {frac*100:>9.0f}% {v:>6s}')
    (good if frac >= 0.5 else weak).append(n)

print()
print('有效对:', sorted(good), len(good), '个')
print('弱/无效:', sorted(weak), len(weak), '个')
