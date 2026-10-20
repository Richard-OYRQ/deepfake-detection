# -*- coding: utf-8 -*-
"""验证 _repro21.mp4 的换脸情况（直接比对法）。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

OUT = r'D:\deepfake\pairset\outputs\_repro21.mp4'
ORI = r'D:\deepfake\videos\21.mp4'

cap_o = cv2.VideoCapture(OUT)
cap_r = cv2.VideoCapture(ORI)
swapped = checked = 0
for ts in (0.3, 0.8, 1.3, 1.8, 2.3, 2.8, 3.3, 3.8, 4.3, 4.8):
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
    d_bg = float(np.abs(fo[20:220, 20:220].astype(np.float32)
                        - fr[20:220, 20:220].astype(np.float32)).mean())
    is_swap = d_face > d_bg * 3
    checked += 1
    swapped += int(is_swap)
    print(f't={ts:>4.1f}s: 人脸区差={d_face:5.1f} 背景区差={d_bg:5.1f} → {"已换脸" if is_swap else "未换脸"}')
cap_o.release()
cap_r.release()
print(f'结论: {swapped}/{checked} 帧已换脸')
