# -*- coding: utf-8 -*-
"""人脸+面颈裁剪模块（缓存构建与评估共用，保证训练/考试口径一致）。
用 insightface 检测最大人脸，裁 1.4 倍人脸框并向下延伸含颈部；
无脸帧返回原帧（标记 found=False），保证无数据丢失。"""
import glob
import os
import sys

_site = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages")
for _d in glob.glob(os.path.join(_site, "nvidia", "*", "bin")):
    try:
        os.add_dll_directory(_d)
    except OSError:
        pass

from insightface.app import FaceAnalysis  # noqa: E402

_app = None


def get_app():
    global _app
    if _app is None:
        _app = FaceAnalysis(name="buffalo_l", root=r"E:\deepfake\_swap_models",
                            providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        _app.prepare(ctx_id=0, det_size=(640, 640))
    return _app


def crop_face_neck(frame):
    """返回 (裁剪图, 是否检出人脸)。无脸时返回原帧。"""
    faces = get_app().get(frame)
    if not faces:
        return frame, False
    f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
    x1, y1, x2, y2 = [int(v) for v in f.bbox]
    w, h = x2 - x1, y2 - y1
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    half_w = max(int(w * 0.7), 32)
    top = max(0, cy - int(h * 0.8))            # 上方留额头
    bot = min(frame.shape[0], cy + int(h * 1.4))  # 下方含颈部
    left = max(0, cx - half_w)
    right = min(frame.shape[1], cx + half_w)
    return frame[top:bot, left:right], True
