# -*- coding: utf-8 -*-
"""多位置扫描验证换脸：输出视频 8 个时间点的人脸分别与源脸/原脸比相似度。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

CASES = [('2', r'D:\deepfake\pairset\outputs\fake_e2_on_2.mp4'),
         ('21', r'D:\deepfake\pairset\outputs\fake_e21_on_21.mp4')]


def face_crop(frame):
    r = _detect_face(frame)
    if r is None:
        return None
    x, y, fw, fh = r
    return frame[y:y + fh, x:x + fw]


def face_img(p):
    img = cv2.imread(p)
    if img is None:
        return None
    return face_crop(img)


def sim(a, b):
    a = cv2.resize(a, (64, 64), interpolation=cv2.INTER_AREA)
    b = cv2.resize(b, (64, 64), interpolation=cv2.INTER_AREA)
    a = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32).flatten()
    b = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32).flatten()
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    return float(np.dot(a, b) / len(a))


for tag, out_vid in CASES:
    src_p = r'D:\deepfake\exface\%s.jpg' % tag
    tgt_p = r'D:\deepfake\videos\%s.mp4' % tag
    f_src = face_img(src_p)
    cap = cv2.VideoCapture(out_vid)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    cap_t = cv2.VideoCapture(tgt_p)
    tt = int(cap_t.get(cv2.CAP_PROP_FRAME_COUNT))
    tfps = cap_t.get(cv2.CAP_PROP_FPS) or 30.0
    tdur = tt / tfps
    print(f'=== {tag}（输出时长 {dur:.1f}s）===')
    for frac in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        got = _read_frame_at(cap, dur * frac)
        if got is None:
            continue
        _, frame = got
        fo = face_crop(frame)
        if fo is None:
            print(f'  t={frac:.1f}: 输出帧无脸')
            continue
        s1 = sim(fo, f_src)
        # 原脸对比（原视频同比例时间）
        got2 = _read_frame_at(cap_t, tdur * frac)
        s2 = -2.0
        if got2 is not None:
            _, frame2 = got2
            ft = face_crop(frame2)
            if ft is not None:
                s2 = sim(fo, ft)
        verdict = '假脸' if s1 > s2 else '原脸'
        print(f'  t={frac:.1f}: vs源脸={s1:+.3f} vs原脸={s2:+.3f} → {verdict}')
    cap.release()
    cap_t.release()
