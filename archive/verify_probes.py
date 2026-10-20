# -*- coding: utf-8 -*-
"""批量验证 20 个探针输出的换脸情况（直接比对法）。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

NUMS = [2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23]
PAIR = r'D:\deepfake\pairset'


def check_one(n):
    out = os.path.join(PAIR, 'outputs', 'probe_%d.mp4' % n)
    ori = os.path.join(r'D:\deepfake\videos', '%d.mp4' % n)
    if not os.path.exists(out):
        return None
    cap_o = cv2.VideoCapture(out)
    cap_r = cv2.VideoCapture(ori)
    vals = []
    for ts in (0.3, 0.6, 0.9, 1.2, 1.5, 1.8):
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


working, failing = [], []
print(f'{"编号":>4s} {"人脸/背景差比(6帧)":>30s} {"判定":>8s}')
for n in NUMS:
    vals = check_one(n)
    if vals is None:
        print(f'{n:>4d}  无输出')
        failing.append(n)
        continue
    ratio = np.median(vals)
    swapped = sum(1 for v in vals if v > 2.5)
    verdict = '生效' if swapped >= 3 else '边缘' if swapped >= 1 else '未生效'
    print(f'{n:>4d}  {["%.1f" % v for v in vals]!s:>30s} {verdict:>8s} ({swapped}/6)')
    (working if swapped >= 3 else failing).append(n)

print()
print('可换脸视频:', sorted(working), len(working), '个')
print('失效视频:', sorted(failing), len(failing), '个')
