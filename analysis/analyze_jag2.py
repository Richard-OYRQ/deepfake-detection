# -*- coding: utf-8 -*-
"""锯齿指纹 v2：轮廓位置的"之字形交替率"（1px台阶计入门槛）。
锯齿状边缘 = 位置序列快速反向交替（+1/-1/±1…）；自然轮廓 = 同向渐变。
4对样本验证：e10/e5/e14/e22。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'
PAIRS = [10, 5, 14, 22]


def zigzag_rate(band):
    """轮廓位置序列的之字形交替率。"""
    grad = np.abs(np.diff(band, axis=1))
    pos = np.argmax(grad, axis=1).astype(np.float32)
    steps = np.diff(pos)
    s = steps[steps != 0]
    if len(s) < 10:
        return 0.0
    signs = np.sign(s)
    # 相邻非零步方向交替的比例（|步长|≥1 全部计入）
    altern = (signs[1:] != signs[:-1]).mean()
    return float(altern)


def frame_metrics(frame, rect):
    x, y, fw, fh = rect
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    y1 = y + int(fh * 0.15)
    y2 = y + int(fh * 0.75)
    if y2 - y1 < 30:
        return None
    rates = []
    for side in (-1, 1):
        bx = x + (fw if side > 0 else 0)
        x1 = max(0, bx - 20)
        x2 = min(w, bx + 20)
        if x2 - x1 < 20:
            continue
        rates.append(zigzag_rate(gray[y1:y2, x1:x2]))
    # 下颌线
    yy1 = y + int(fh * 0.85)
    yy2 = min(h, y + fh + int(fh * 0.2))
    if yy2 - yy1 >= 20:
        x1 = max(0, x - int(fw * 0.15))
        x2 = min(w, x + fw + int(fw * 0.15))
        rates.append(zigzag_rate(gray[yy1:yy2, x1:x2].T))
    return tuple(rates) if rates else None


def video_stats(path):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    vals = []
    ts = 0.1
    while ts < dur - 0.1:
        got = _read_frame_at(cap, ts)
        if got is not None:
            _, fr = got
            r = _detect_face(fr)
            if r is not None:
                m = frame_metrics(fr, r)
                if m is not None:
                    vals.append(m)
        ts += 0.2
    cap.release()
    return np.array(vals) if vals else None


print(f'{"对":>4s} {"真·之字率均值":>14s} {"假·之字率均值":>14s} {"差值":>8s} {"方向":>4s}')
for n in PAIRS:
    tr = video_stats(os.path.join(BASE, 'videos', '%d.mp4' % n))
    tf = video_stats(os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))
    if tr is None or tf is None:
        print(n, '数据不足')
        continue
    m_r = tr.mean(axis=0)
    m_f = tf.mean(axis=0)
    d = m_f - m_r
    direction = '假更高' if d.mean() > 0.01 else '假更低' if d.mean() < -0.01 else '持平'
    print(f'{n:>4d} {np.round(m_r, 3)!s:>14s} {np.round(m_f, 3)!s:>14s} {np.round(d, 3)!s:>8s} {direction:>4s}')
    print(f'     左/右/下颌: 真{m_r[0]:.3f}/{m_r[1]:.3f}/{m_r[2]:.3f}  假{m_f[0]:.3f}/{m_f[1]:.3f}/{m_f[2]:.3f}')
