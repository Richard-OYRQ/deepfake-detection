# -*- coding: utf-8 -*-
"""从 FF++ c23 压缩包远程抽取 300真实 + 300伪造（6方法×50），补齐外部评测集到 500+500。"""
import os
import random
import sys
import time
from remotezip import RemoteZip

MAX_NEW = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 每轮最多新下载数，0=不限

URL = "https://hf-mirror.com/datasets/bitmind/FaceForensicsC23/resolve/main/FaceForensics%2B%2B_C23.zip"
OUT = r"E:\DeepFake\外部评测集100"
random.seed(43)

z = RemoteZip(URL, headers={"User-Agent": "Mozilla/5.0"})
infos = [i for i in z.infolist() if i.filename.endswith(".mp4")]

reals = sorted([i for i in infos if "/real/" in i.filename], key=lambda x: x.filename)
picks = [(i, "real", i.filename.split("/")[-1]) for i in random.sample(reals, 300)]

methods = ["DeepFakeDetection", "Deepfakes", "Face2Face", "FaceShifter", "FaceSwap", "NeuralTextures"]
for m in methods:
    ms = [i for i in infos if f"/fake/{m}/" in i.filename]
    for i in random.sample(ms, 50):
        picks.append((i, "fake", f"{m}_{i.filename.split('/')[-1]}"))

def fetch_to(info, dest):
    for attempt in range(3):
        try:
            with z.open(info) as src, open(dest, "wb") as dst:
                import shutil
                shutil.copyfileobj(src, dst, length=1 << 20)  # 流式，1MB 缓冲
            return True
        except Exception as e:
            if attempt == 2:
                print("  (最后尝试失败)", flush=True)
                return False
            time.sleep(3)

ok, fail, total_bytes = 0, 0, 0
for n, (info, label, fname) in enumerate(picks, 1):
    dest_dir = os.path.join(OUT, label)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        continue
    if MAX_NEW and ok >= MAX_NEW:
        break
    if fetch_to(info, dest):
        ok += 1
        total_bytes += os.path.getsize(dest)
        print(f"[{n}/{len(picks)}] OK  {label}/{fname}  {os.path.getsize(dest)//1024}KB", flush=True)
    else:
        fail += 1
        print(f"[{n}/{len(picks)}] FAIL {fname}", flush=True)
    if n % 20 == 0:
        time.sleep(5)  # 每 20 个缓一缓，减轻内存压力

print(f"\n完成: 成功 {ok}, 失败 {fail}, 新下载 {total_bytes//1024//1024}MB", flush=True)
