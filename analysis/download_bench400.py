# -*- coding: utf-8 -*-
"""补齐 angads24/deepfake-video 剩余 150真实+150伪造，使外部评测集达到 200+200=400。"""
import json
import os
import urllib.parse
import urllib.request

BASE = "https://hf-mirror.com/datasets/angads24/deepfake-video/resolve/main/"
OUT = r"E:\DeepFake\外部评测集100"
MIRROR_JSON = os.path.join(os.environ["TEMP"], "adtree.json")

tree = json.load(open(MIRROR_JSON, encoding="utf-8-sig"))
all_real = [f["path"] for f in tree if f.get("type") == "file" and "/real/" in f["path"]]
all_fake = [f["path"] for f in tree if f.get("type") == "file" and "/fake/" in f["path"]]

picks = [(p, "real") for p in all_real] + [(p, "fake") for p in all_fake]

ok, skip, fail = 0, 0, 0
for i, (path, label) in enumerate(picks, 1):
    fname = path.split("/")[-1]
    dest_dir = os.path.join(OUT, label)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        skip += 1
        continue
    url = BASE + urllib.parse.quote(path)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
            f.write(r.read())
        ok += 1
        print(f"[{i}/{len(picks)}] OK   {label}/{fname}  {os.path.getsize(dest)//1024}KB", flush=True)
    except Exception as e:
        fail += 1
        print(f"[{i}/{len(picks)}] FAIL {label}/{fname}: {e}", flush=True)

print(f"\n完成: 新下载 {ok}, 跳过已有 {skip}, 失败 {fail}", flush=True)
