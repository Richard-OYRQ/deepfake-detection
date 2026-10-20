# -*- coding: utf-8 -*-
"""批量验证 20 个输出的换脸生效性：输出脸 vs 源脸 / 输出脸 vs 目标原脸。"""
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


def face_from_vid(p, fracs=(0.25, 0.5, 0.75)):
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


def face_from_img(p):
    img = cv2.imread(p)
    if img is None:
        return None
    r = _detect_face(img)
    if r is None:
        return None
    x, y, fw, fh = r
    return img[y:y + fh, x:x + fw]


def sim(a, b):
    a = cv2.resize(a, (64, 64), interpolation=cv2.INTER_AREA)
    b = cv2.resize(b, (64, 64), interpolation=cv2.INTER_AREA)
    a = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32).flatten()
    b = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32).flatten()
    a = (a - a.mean()) / (a.std() + 1e-9)
    b = (b - b.mean()) / (b.std() + 1e-9)
    return float(np.dot(a, b) / len(a))


ok, fail = [], []
print(f'{"编号":>4s} {"vs源脸":>8s} {"vs原脸":>8s} {"判定":>8s}')
for n in NUMS:
    src = None
    for ext in ('.jpg', '.png', '.jpeg', '.webp'):
        c = os.path.join(PAIR, '..', 'exface', '%d%s' % (n, ext))
        c = os.path.normpath(c)
        if os.path.exists(c):
            src = c
            break
    out = os.path.join(PAIR, 'outputs', 'fake_e%d_on_%d.mp4' % (n, n))
    tgt = os.path.join(PAIR, '..', 'videos', '%d.mp4' % n)
    tgt = os.path.normpath(tgt)
    f_out = face_from_vid(out)
    f_src = face_from_img(src) if src else None
    f_tgt = face_from_vid(tgt)
    if f_out is None or f_src is None or f_tgt is None:
        print(f'{n:>4d}  {"检测失败":>8s} (out={f_out is not None} src={f_src is not None} tgt={f_tgt is not None})')
        fail.append(n)
        continue
    s1, s2 = sim(f_out, f_src), sim(f_out, f_tgt)
    v = '生效' if s1 > s2 else '未生效'
    print(f'{n:>4d} {s1:>8.3f} {s2:>8.3f} {v:>8s}')
    (ok if v == '生效' else fail).append(n)

print()
print('换脸生效:', sorted(ok), len(ok), '个')
print('未生效/失败:', sorted(fail), len(fail), '个')
