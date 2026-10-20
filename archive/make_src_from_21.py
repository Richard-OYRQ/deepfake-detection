# -*- coding: utf-8 -*-
"""从 videos/21.mp4 抽一张清晰人脸帧作为测试源脸。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2

from src.preprocessor import _detect_face, _read_frame_at

cap = cv2.VideoCapture(r'D:\deepfake\videos\21.mp4')
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
dur = total / fps
best = None
for f in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7):
    got = _read_frame_at(cap, dur * f)
    if got is None:
        continue
    _, frame = got
    r = _detect_face(frame)
    if r is not None:
        area = r[2] * r[3]
        if best is None or area > best[0]:
            best = (area, frame, r)
cap.release()
_, frame, (x, y, fw, fh) = best
cx, cy = x + fw / 2, y + fh / 2
side = int(max(fw, fh) * 2.0)
x1, y1 = max(0, int(cx - side / 2)), max(0, int(cy - side / 2))
x2, y2 = min(frame.shape[1], int(cx + side / 2)), min(frame.shape[0], int(cy + side / 2))
cv2.imwrite(r'D:\deepfake\pairset\sources\src_from21.jpg', frame[y1:y2, x1:x2],
            [int(cv2.IMWRITE_JPEG_QUALITY), 95])
print('saved src_from21.jpg', frame[y1:y2, x1:x2].shape)
