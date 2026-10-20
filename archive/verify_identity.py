# -*- coding: utf-8 -*-
"""验证 exface/N 是否就是 videos/N 中同一位人物（同人换同人的假设检验）。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

CASES = [
    ('1', r'D:\deepfake\exface\1.jpg', r'D:\deepfake\videos\1.mp4'),
    ('4', r'D:\deepfake\exface\4.jpg', r'D:\deepfake\videos\4.mp4'),
    ('21', r'D:\deepfake\exface\21.jpg', r'D:\deepfake\videos\21.mp4'),
]


def face_from_img(p):
    img = cv2.imread(p)
    r = _detect_face(img)
    if r is None:
        return None
    x, y, fw, fh = r
    return img[y:y + fh, x:x + fw]


def face_from_vid(p, fracs=(0.3, 0.5, 0.7)):
    cap = cv2.VideoCapture(p)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    for f in fracs:
        got = _read_frame_at(cap, dur * f)
        if got is None:
            continue
        _, frame = got
        r = _detect_face(frame)
        if r is not None:
            x, y, fw, fh = r
            cap.release()
            return frame[y:y + fh, x:x + fw]
    cap.release()
    return None


def sim(a, b):
    a = cv2.resize(a, (64, 64), interpolation=cv2.INTER_AREA)
    b = cv2.resize(b, (64, 64), interpolation=cv2.INTER_AREA)
    a = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32).flatten()
    b = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32).flatten()
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    return float(np.dot(a, b) / len(a))


for tag, img_p, vid_p in CASES:
    fi = face_from_img(img_p)
    fv = face_from_vid(vid_p)
    if fi is None or fv is None:
        print(f'{tag}: 人脸检测失败 (img={fi is not None}, vid={fv is not None})')
        continue
    s = sim(fi, fv)
    print(f'{tag}: exface与videos人脸相似度 = {s:.3f}  →  {"同人（换脸=同人换同人，结果近似原视频）" if s > 0.3 else "不同人（换脸应有效）"}')
