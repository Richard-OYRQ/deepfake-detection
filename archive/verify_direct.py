# -*- coding: utf-8 -*-
"""决定性验证：输出帧 vs 原视频同帧——人脸区域与背景区域的相似度对比。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

OUT = r'D:\deepfake\pairset\outputs\_debug2.mp4'
ORI = r'D:\deepfake\videos\2.mp4'


def norm_corr(a, b):
    a = cv2.resize(a, (64, 64), interpolation=cv2.INTER_AREA)
    b = cv2.resize(b, (64, 64), interpolation=cv2.INTER_AREA)
    a = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32).flatten()
    b = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32).flatten()
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    return float(np.dot(a, b) / len(a))


cap_o = cv2.VideoCapture(OUT)
cap_r = cv2.VideoCapture(ORI)
for ts in (0.5, 1.0, 1.5):
    go = _read_frame_at(cap_o, ts)
    gr = _read_frame_at(cap_r, ts)
    if go is None or gr is None:
        continue
    _, fo = go
    _, fr = gr
    # 背景块（左上角，避开人脸）
    bg_o = fo[20:220, 20:220]
    bg_r = fr[20:220, 20:220]
    s_bg = norm_corr(bg_o, bg_r)
    # 人脸区域（以原视频帧检测到的人脸框为准）
    r = _detect_face(fr)
    if r is None:
        print(f't={ts}s: 原视频无脸')
        continue
    x, y, fw, fh = r
    face_o = fo[y:y + fh, x:x + fw]
    face_r = fr[y:y + fh, x:x + fw]
    s_face = norm_corr(face_o, face_r)
    # 逐像素绝对差均值（人脸区域）
    d_face = float(np.abs(face_o.astype(np.float32) - face_r.astype(np.float32)).mean())
    d_bg = float(np.abs(bg_o.astype(np.float32) - bg_r.astype(np.float32)).mean())
    print(f't={ts}s: 背景相关={s_bg:.3f} 人脸相关={s_face:.3f} | 人脸区像素差={d_face:.1f} 背景区像素差={d_bg:.1f} '
          f'→ {"已换脸" if d_face > d_bg * 3 else "未换脸"}')
cap_o.release()
cap_r.release()
