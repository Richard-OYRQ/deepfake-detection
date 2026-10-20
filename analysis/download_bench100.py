# -*- coding: utf-8 -*-
"""从 angads24/deepfake-video 下载 50 真实 + 50 伪造 共 100 个视频（hf-mirror 镜像）。"""
import json
import os
import random
import sys
import urllib.request

BASE = "https://hf-mirror.com/datasets/angads24/deepfake-video/resolve/main/"
OUT = r"E:\DeepFake\外部评测集100"
MIRROR_JSON = os.path.join(os.environ["TEMP"], "adtree.json")

random.seed(42)

tree = json.load(open(MIRROR_JSON, encoding="utf-8-sig"))
real = [f["path"] for f in tree if f.get("type") == "file" and "/real/" in f["path"]]
fake = [f["path"] for f in tree if f.get("type") == "file" and "/fake/" in f["path"]]
picks = [(p, "real") for p in random.sample(real, 50)] + \
        [(p, "fake") for p in random.sample(fake, 50)]

ok, fail = 0, 0
for i, (path, label) in enumerate(picks, 1):
    fname = path.split("/")[-1]
    dest_dir = os.path.join(OUT, label)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        ok += 1
        continue
    url = BASE + urllib.parse.quote(path)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            f.write(r.read())
        ok += 1
        print(f"[{i}/100] OK  {label}/{fname}  {os.path.getsize(dest)//1024}KB")
    except Exception as e:
        fail += 1
        print(f"[{i}/100] FAIL {label}/{fname}: {e}")

print(f"\n完成: 成功 {ok}, 失败 {fail}")
