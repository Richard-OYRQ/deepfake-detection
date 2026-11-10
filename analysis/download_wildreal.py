# -*- coding: utf-8 -*-
"""从 WildDeepfake 数据集下载 100 个 real_train 人脸序列（挑 ≤120MB 的包，约 5GB）。
来源：hf-mirror.com/xingjunm/WildDeepfake（互联网野生视频，标签按目录已分）。"""
import json
import os
import random
import shutil
import time

import requests

H = {"User-Agent": "Mozilla/5.0"}
API = "https://hf-mirror.com/api/datasets/xingjunm/WildDeepfake/tree/main/deepfake_in_the_wild/real_train"
BASE = "https://hf-mirror.com/datasets/xingjunm/WildDeepfake/resolve/main/deepfake_in_the_wild/real_train"
OUT = r"E:\deepfake\_wildreal"
os.makedirs(OUT, exist_ok=True)
random.seed(20261111)

d = requests.get(API, headers=H, timeout=60).json()
files = [x for x in d if x.get("type") == "file" and (x.get("size") or 0) <= 120e6]
print(f"候选 {len(files)} 个（≤120MB）", flush=True)
picks = random.sample(files, min(100, len(files)))

ok = fail = 0
for i, x in enumerate(picks, 1):
    name = x["path"].split("/")[-1]
    dest = os.path.join(OUT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 1e6:
        ok += 1
        continue
    try:
        r = requests.get(f"{BASE}/{name}", headers=H, timeout=600, stream=True)
        if r.status_code != 200:
            print(f"[{i}] HTTP {r.status_code} {name}", flush=True)
            fail += 1
            continue
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        ok += 1
    except Exception as e:
        print(f"[{i}] 失败 {name}: {type(e).__name__}", flush=True)
        fail += 1
    if i % 10 == 0 or i == len(picks):
        print(f"[{i}/{len(picks)}] 完成 {ok} 失败 {fail}", flush=True)
    time.sleep(0.5)

print(f"全部结束：成功 {ok}，失败 {fail} -> {OUT}", flush=True)
