# -*- coding: utf-8 -*-
"""核实视频分辨率与人脸像素大小（分辨率≠人脸分辨率）。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2

from src.preprocessor import _detect_face, _read_frame_at

SAMPLES = ['待鉴别/F89.mp4', '待鉴别/F97.mp4', '待鉴别/F99.mp4',
           'videos/15.mp4', 'videos/63.mp4', 'videos/1.mp4', 'videos/96.mp4']

for rel in SAMPLES:
    p = os.path.join(r'D:\deepfake', rel)
    cap = cv2.VideoCapture(p)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    size_mb = os.path.getsize(p) / 1024 / 1024
    dur = nf / fps if fps else 0
    # 抽 3 帧看人脸框大小（复用同一 cap）
    faces = []
    for ts in (dur * 0.25, dur * 0.5, dur * 0.75):
        got = _read_frame_at(cap, ts)
        if got is None:
            continue
        _, frame = got
        r = _detect_face(frame)
        if r is not None:
            faces.append(r[2])
    cap.release()
    fstr = '/'.join(str(f) for f in faces) if faces else '无脸'
    bitrate = size_mb * 8 / dur if dur else 0
    print(f'{rel:<20s} {w}x{h}  {dur:.1f}s  {size_mb:.1f}MB ({bitrate:.1f}Mbps)  人脸框宽(px): {fstr}')
