# -*- coding: utf-8 -*-
"""从 FF++ c23 压缩包再抽 500 条第一代换脸伪造视频：
Deepfakes 167 + FaceSwap 167 + DeepFakeDetection 166，排除已下载文件。
沿用 download_bench1100.py 的 remotezip 流式抽文件方案，seed=20261021。"""
import os
import random
import shutil
import time
from remotezip import RemoteZip

URL = "https://hf-mirror.com/datasets/bitmind/FaceForensicsC23/resolve/main/FaceForensics%2B%2B_C23.zip"
OUT = r"E:\DeepFake\外部评测集100"
random.seed(20261021)

existing_fake = set(os.listdir(os.path.join(OUT, "fake")))

def open_zip(retries=6):
    """429 限流时指数退避重试：60s/120s/240s... 最长等待约 21 分钟。"""
    for attempt in range(1, retries + 1):
        try:
            return RemoteZip(URL, headers={"User-Agent": "Mozilla/5.0"})
        except Exception as e:
            wait = 60 * 2 ** (attempt - 1)
            print(f"初始化被限流，{wait}s 后重试（{attempt}/{retries}）：{type(e).__name__}",
                  flush=True)
            time.sleep(wait)
    raise RuntimeError("多次重试仍被限流，请稍后再运行本脚本")


z = open_zip()
infos = [i for i in z.infolist() if i.filename.endswith(".mp4")]

# 第一代三家族（DeepFakeDetection 为 Deepfakes 的重压缩实验子集，同属第一代）
methods = ["Deepfakes", "FaceSwap", "DeepFakeDetection"]
per_method = {"Deepfakes": 167, "FaceSwap": 167, "DeepFakeDetection": 166}

picks = []
for m in methods:
    pool = [i for i in infos if f"/fake/{m}/" in i.filename
            and f"{m}_{i.filename.split('/')[-1]}" not in existing_fake]
    n = min(per_method[m], len(pool))
    print(f"{m} 候选 {len(pool)} 条，抽取 {n} 条", flush=True)
    for i in random.sample(pool, n):
        picks.append((i, f"{m}_{i.filename.split('/')[-1]}"))

print(f"共 {len(picks)} 条待下载", flush=True)


def fetch_to(info, dest):
    for attempt in range(3):
        try:
            with z.open(info) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst, length=1 << 20)  # 流式，1MB 缓冲
            return True
        except Exception:
            if attempt == 2:
                return False
            time.sleep(3)


ok = fail = 0
dest_dir = os.path.join(OUT, "fake")
for n, (info, fname) in enumerate(picks, 1):
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        ok += 1
        continue
    if fetch_to(info, dest):
        ok += 1
    else:
        fail += 1
        print(f"  FAIL {fname}", flush=True)
    time.sleep(0.3)  # 对镜像站限速，避免再次触发 429
    if n % 25 == 0 or n == len(picks):
        print(f"[{n}/{len(picks)}] 完成 {ok} / 失败 {fail}", flush=True)

print(f"全部结束：成功 {ok}，失败 {fail}，输出目录 {OUT}", flush=True)
