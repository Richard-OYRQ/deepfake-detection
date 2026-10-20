# -*- coding: utf-8 -*-
"""e10 vs 10 逐帧之字率时间序列（左边界）。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'


def zigzag_rate(band):
    grad = np.abs(np.diff(band, axis=1))
    pos = np.argmax(grad, axis=1).astype(np.float32)
    steps = np.diff(pos)
    s = steps[steps != 0]
    if len(s) < 10:
        return 0.0
    signs = np.sign(s)
    return float((signs[1:] != signs[:-1]).mean())


def series(path):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    out = []
    ts = 0.1
    while ts < dur - 0.1:
        got = _read_frame_at(cap, ts)
        if got is not None:
            _, fr = got
            r = _detect_face(fr)
            if r is not None:
                x, y, fw, fh = r
                h, w = fr.shape[:2]
                gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32)
                y1, y2 = y + int(fh * 0.15), y + int(fh * 0.75)
                if y2 - y1 >= 30:
                    band = gray[y1:y2, max(0, x - 20):min(w, x + 20)]
                    out.append((round(ts, 1), zigzag_rate(band)))
        ts += 0.2
    cap.release()
    return out


real = series(os.path.join(BASE, 'videos', '10.mp4'))
fake = series(os.path.join(BASE, 'pairset', 'outputs', 'fake_e10_on_10.mp4'))
print('t(s) | 真·之字率 | 假·之字率 | 差')
for i in range(0, max(len(real), len(fake)), 4):
    rr = real[i][1] if i < len(real) else float('nan')
    ff = fake[i][1] if i < len(fake) else float('nan')
    print('%4.1f | %9.3f | %9.3f | %+.3f' % (real[i][0], rr, ff, ff - rr))
