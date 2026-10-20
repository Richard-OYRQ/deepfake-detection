# -*- coding: utf-8 -*-
"""密集扫描 6 条零信号视频：Haar 默认参数 vs 宽松参数，每 0.5s 一帧全片扫。"""
import cv2
import sys

sys.path.insert(0, r"E:\deepfake\src")

V = ["63", "88", "96", "F63", "F88", "F96"]

# 用 preprocessor 已加载的 Haar 检测器（默认参数），另建宽松参数检测器
from preprocessor import _face_detector  # noqa: E402

for v in V:
    cap = cv2.VideoCapture(rf"E:\deepfake\videos\{v}.mp4")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n_hits_def = n_hits_loose = n_frames = 0
    sizes = []
    t = 0.0
    while True:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        n_frames += 1
        h, w = frame.shape[:2]
        max_dim = 1920
        if max(w, h) > max_dim:
            s = max_dim / max(w, h)
            frame = cv2.resize(frame, (int(w * s), int(h * s)))
            h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        min_face = max(60, min(w, h) // 8)
        faces = _face_detector.detectMultiScale(gray, 1.1, 5,
                                                minSize=(min_face, min_face),
                                                maxSize=(min(w, h) // 2, min(w, h) // 2))
        if len(faces):
            n_hits_def += 1
            sizes.append((faces[0][2], faces[0][3]))
        faces2 = _face_detector.detectMultiScale(gray, 1.05, 3, minSize=(40, 40))
        if len(faces2):
            n_hits_loose += 1
        t += 0.5
    cap.release()
    sizes_s = ", ".join(f"{a}x{b}" for a, b in sizes[:5])
    print(f"{v}: 扫帧{n_frames} 默认参数命中{n_hits_def} 宽松参数命中{n_hits_loose}  "
          f"检出人脸尺寸样例[{sizes_s}]")
