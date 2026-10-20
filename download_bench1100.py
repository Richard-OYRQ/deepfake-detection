# -*- coding: utf-8 -*-
"""从 FF++ c23 压缩包再抽 50 真实 + 50 伪造（6方法×8~9），外部评测集补齐到 550+550。seed=44，排除已下载文件。"""
import os
import random
import shutil
import time
from remotezip import RemoteZip

URL = "https://hf-mirror.com/datasets/bitmind/FaceForensicsC23/resolve/main/FaceForensics%2B%2B_C23.zip"
OUT = r"E:\DeepFake\外部评测集100"
random.seed(44)

existing_real = set(os.listdir(os.path.join(OUT, "real")))
existing_fake = set(os.listdir(os.path.join(OUT, "fake")))

z = RemoteZip(URL, headers={"User-Agent": "Mozilla/5.0"})
infos = [i for i in z.infolist() if i.filename.endswith(".mp4")]

# 真实：排除已下载，随机抽 50
reals = sorted([i for i in infos if "/real/" in i.filename], key=lambda x: x.filename)
real_pool = [i for i in reals if i.filename.split("/")[-1] not in existing_real]
print(f"真实候选 {len(real_pool)} 条，抽取 50 条")
picks = [(i, "real", i.filename.split("/")[-1]) for i in random.sample(real_pool, 50)]

# 伪造：6 种方法各再抽 8~9，避开已下载（已存文件带方法名前缀）
methods = ["DeepFakeDetection", "Deepfakes", "Face2Face", "FaceShifter", "FaceSwap", "NeuralTextures"]
per_method = {"DeepFakeDetection": 9, "Deepfakes": 9, "Face2Face": 8,
              "FaceShifter": 8, "FaceSwap": 8, "NeuralTextures": 8}
for m in methods:
    pool = [i for i in infos if f"/fake/{m}/" in i.filename
            and f"{m}_{i.filename.split('/')[-1]}" not in existing_fake]
    print(f"{m} 候选 {len(pool)} 条，抽取 {per_method[m]} 条")
    for i in random.sample(pool, per_method[m]):
        picks.append((i, "fake", f"{m}_{i.filename.split('/')[-1]}"))

def fetch_to(info, dest):
    for attempt in range(3):
        try:
            with z.open(info) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst, length=1 << 20)  # 流式，1MB 缓冲
            return True
        except Exception as e:
            if attempt == 2:
                print("  (最后尝试失败)", flush=True)
                return False
            time.sleep(3)

ok, fail = 0, 0
for n, (info, label, fname) in enumerate(picks, 1):
    dest_dir = os.path.join(OUT, label)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        continue
    if fetch_to(info, dest):
        ok += 1
        print(f"[{n}/{len(picks)}] OK  {label}/{fname}  {os.path.getsize(dest)//1024}KB", flush=True)
    else:
        fail += 1
        print(f"[{n}/{len(picks)}] FAIL {fname}", flush=True)
    if n % 20 == 0:
        time.sleep(5)  # 每 20 个缓一缓

print(f"\n完成: 成功 {ok}, 失败 {fail}", flush=True)
