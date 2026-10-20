# -*- coding: utf-8 -*-
"""配对样本验证：输出视频规格 + 换脸生效性（归一化互相关粗检）。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

PAIR = r'D:\deepfake\pairset'
CASES = [
    ('fake_e1_on_1', r'D:\deepfake\exface\1.jpg', r'D:\deepfake\videos\1.mp4'),
    ('fake_e4_on_4', r'D:\deepfake\exface\4.jpg', r'D:\deepfake\videos\4.mp4'),
    ('fake_e21_on_21', r'D:\deepfake\exface\21.jpg', r'D:\deepfake\videos\21.mp4'),
]


def face_crop_from_video(path, frac=0.5):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    got = _read_frame_at(cap, dur * frac)
    cap.release()
    if got is None:
        return None
    _, frame = got
    r = _detect_face(frame)
    if r is None:
        return None
    x, y, fw, fh = r
    return frame[y:y + fh, x:x + fw]


def face_crop_from_image(path):
    img = cv2.imread(path)
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


print('===== 输出视频规格 =====')
for name, _, _ in CASES:
    p = os.path.join(PAIR, 'outputs', name + '.mp4')
    cap = cv2.VideoCapture(p)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    print(f'  {name}: {w}x{h}  {fps:.1f}fps  {nf}帧  {nf/fps:.1f}s')

print()
print('===== 换脸生效性（人脸归一化互相关） =====')
print(f'{"样本":<18s} {"输出脸vs源脸":>14s} {"输出脸vs目标原脸":>18s} {"判定":>8s}')
for name, src_img, tgt_vid in CASES:
    out_vid = os.path.join(PAIR, 'outputs', name + '.mp4')
    f_out = face_crop_from_video(out_vid)
    f_src = face_crop_from_image(src_img)
    f_tgt = face_crop_from_video(tgt_vid)
    if f_out is None or f_src is None or f_tgt is None:
        print(f'  {name}: 人脸检测失败 (out={f_out is not None} src={f_src is not None} tgt={f_tgt is not None})')
        continue
    s1 = sim(f_out, f_src)
    s2 = sim(f_out, f_tgt)
    verdict = '换脸生效' if s1 > s2 else '未生效/存疑'
    print(f'  {name:<18s} {s1:>14.3f} {s2:>18.3f} {verdict:>8s}')
