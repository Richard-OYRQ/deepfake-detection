# -*- coding: utf-8 -*-
"""自建集抽样：真伪各 30 条（排除 exp6 用过的 6 条伪造），复制到 _self60，写 labels.json。"""
import json
import os
import random
import shutil

random.seed(20261011)
OUT = r"E:\deepfake\_self60"
os.makedirs(OUT, exist_ok=True)

vids = [f for f in os.listdir(r"E:\deepfake\videos")
        if f.endswith(".mp4") and os.path.isfile(os.path.join(r"E:\deepfake\videos", f))]
reals = sorted(f for f in vids if f[0].isdigit())
fakes = sorted(f for f in vids if f.startswith("F") and f not in
               (f"F{n}.mp4" for n in (6, 8, 18, 42, 45, 51)))

picks = [(f, "real") for f in random.sample(reals, 30)] + \
        [(f, "fake") for f in random.sample(fakes, 30)]

labels = {}
for f, lab in picks:
    shutil.copy2(os.path.join(r"E:\deepfake\videos", f), os.path.join(OUT, f))
    labels[f] = lab
with open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8") as fp:
    json.dump(labels, fp, ensure_ascii=False, indent=2)
print(f"完成：{len(labels)} 条 → _self60（真实 {sum(1 for v in labels.values() if v=='real')} / "
      f"伪造 {sum(1 for v in labels.values() if v=='fake')}）")
