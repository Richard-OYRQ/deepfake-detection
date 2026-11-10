# -*- coding: utf-8 -*-
"""M1 抽帧缓存：为训练池每条视频抽取 K 帧（时长 20%–80% 均匀分布），
缩放短边 256 后存 JPEG 到 data/frames_cache/。断点续跑（已缓存跳过）。"""
import csv
import os

import cv2

from facecrop import crop_face_neck

BASE = r"E:\deepfake"
CACHE = os.path.join(BASE, "data", "frames_cache")
K = 5
os.makedirs(CACHE, exist_ok=True)

SRCDIR = {
    "videos": os.path.join(BASE, "videos"),
    "待鉴别": os.path.join(BASE, "待鉴别"),
    "外部_real": os.path.join(BASE, "外部评测集100", "real"),
    "外部_fake": os.path.join(BASE, "外部评测集100", "fake"),
}

with open(os.path.join(BASE, "data", "训练池清单.csv"), encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))


def cached_name(nid, i):
    return f"{nid}_{i}.jpg"   # 纯数字命名，规避中文文件名写入失败


done = skip = fail = 0
for n, r in enumerate(rows, 1):
    name = r["文件名"]
    nid = str(n)
    if all(os.path.exists(os.path.join(CACHE, cached_name(nid, i)))
           for i in range(K)):
        skip += 1
        continue
    src = os.path.join(SRCDIR[r["来源"]], name)
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        fail += 1
        print(f"  打不开 {name}", flush=True)
        continue
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    dur = total / fps if fps > 0 else 0
    ok = 0
    for i in range(K):
        t = dur * (0.2 + 0.6 * i / (K - 1)) * 1000  # 20%–80% 均匀
        cap.set(cv2.CAP_PROP_POS_MSEC, t)
        ret, frame = cap.read()
        if not ret:
            continue
        frame, _found = crop_face_neck(frame)   # 人脸+面颈裁剪（无脸回退原帧）
        h, w = frame.shape[:2]
        s = 256 / min(h, w)
        frame = cv2.resize(frame, (int(w * s), int(h * s)),
                           interpolation=cv2.INTER_AREA)
        if not cv2.imwrite(os.path.join(CACHE, cached_name(nid, i)), frame,
                           [int(cv2.IMWRITE_JPEG_QUALITY), 90]):
            continue
        ok += 1
    cap.release()
    if ok == K:
        done += 1
    else:
        fail += 1
        print(f"  帧不足 {name}（{ok}/{K}）", flush=True)
    if n % 100 == 0 or n == len(rows):
        print(f"[{n}/{len(rows)}] 完成 {done} 跳过 {skip} 失败 {fail}", flush=True)

print(f"全部结束：完成 {done}，跳过 {skip}，失败 {fail} -> {CACHE}", flush=True)
