# -*- coding: utf-8 -*-
"""本地 inswapper 批量换脸（与 faceswapvideo.io 同源引擎：insightface buffalo_l + inswapper_128）。
- 输入：_swap_source/ 下 80 条编号素材 + 目标脸/ 7 张目标人脸照片
- 输出：_swap_output/ 编号视频（mp4v 重编码，全帧换脸）
- 目标脸轮换分配（7 张轮流），保证换脸主体多样性。"""
import glob
import os
import sys

# CUDA 13 运行库（nvidia pip wheels）加入 DLL 搜索路径，必须在 import onnxruntime 之前
_site = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages")
for _d in glob.glob(os.path.join(_site, "nvidia", "*", "bin")):
    try:
        os.add_dll_directory(_d)
    except OSError:
        pass

import cv2
import insightface
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

BASE = r"E:\deepfake"
MODEL_ROOT = os.path.join(BASE, "_swap_models")          # FaceAnalysis 根目录
INSWAPPER = os.path.join(MODEL_ROOT, "inswapper_128.onnx")  # 单独放置，避免 insightface 误扫描
SRC = os.path.join(BASE, "_swap_source")
FACES_DIR = os.path.join(SRC, "目标脸")
OUT = os.path.join(BASE, "_swap_output")
os.makedirs(OUT, exist_ok=True)

PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]

app = FaceAnalysis(name="buffalo_l", root=MODEL_ROOT, providers=PROVIDERS)
app.prepare(ctx_id=0, det_size=(640, 640))
swapper = get_model(INSWAPPER, providers=PROVIDERS)
print("模型加载完成", flush=True)

# ---- 目标脸（用 PIL 读取，opencv5 对部分 jpg 解码失败）----
import numpy as np
from PIL import Image

targets = []
for p in sorted(os.listdir(FACES_DIR)):
    try:
        pil = Image.open(os.path.join(FACES_DIR, p)).convert("RGB")
        img = np.asarray(pil)[:, :, ::-1].copy()  # RGB -> BGR
    except Exception:
        continue
    faces = app.get(img)
    if faces:
        targets.append(max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])))
print(f"目标脸载入 {len(targets)} 张", flush=True)
assert targets, "目标脸文件夹里没有可检测的人脸"

# ---- 素材视频 ----
videos = sorted(f for f in os.listdir(SRC) if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv")))
print(f"待处理视频 {len(videos)} 条", flush=True)

for idx, name in enumerate(videos, 1):
    src_path = os.path.join(SRC, name)
    out_path = os.path.join(OUT, f"{idx:02d}_swapped.mp4")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
        print(f"[{idx}/{len(videos)}] 已存在，跳过", flush=True)
        continue
    target = targets[(idx - 1) % len(targets)]
    cap = cv2.VideoCapture(src_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        faces = app.get(frame)
        if faces:
            biggest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            try:
                frame = swapper.get(frame, biggest, target, paste_back=True)
            except Exception:
                pass
        writer.write(frame)
        n += 1
    cap.release()
    writer.release()
    import gc
    gc.collect()  # 每条视频后回收内存，防止长时间运行被系统内存保护终止
    print(f"[{idx}/{len(videos)}] {name} -> {os.path.basename(out_path)}"
          f"（{n}/{total} 帧）", flush=True)

print("全部完成 ->", OUT, flush=True)
