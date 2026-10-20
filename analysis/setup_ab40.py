# -*- coding: utf-8 -*-
"""A/B 抽查采样：从外部评测集取 20 真 + 20 伪（排除 exp4 已用），复制到 _ab40 并写 labels.json。"""
import json
import os
import random
import shutil

BASE = r"E:\deepfake\外部评测集100"
OUT = r"E:\deepfake\_ab40"
random.seed(77)

# exp4 已用过的文件（避免复用）
used = set()
for d in os.listdir(r"E:\deepfake"):
    if d.startswith("_exp4c") and os.path.isdir(os.path.join(r"E:\deepfake", d)):
        for f in os.listdir(os.path.join(r"E:\deepfake", d)):
            if os.path.splitext(f)[1].lower() in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
                used.add(f)

pools = {}
for label in ("real", "fake"):
    pools[label] = [f for f in os.listdir(os.path.join(BASE, label)) if f not in used]
    print(f"{label}: 池 {len(pools[label])} 条（已排除 exp4 用过的 {sum(1 for f in used if f in os.listdir(os.path.join(BASE, label)))} 条）")

os.makedirs(OUT, exist_ok=True)
labels = {}
for label, prefix in (("real", "R"), ("fake", "F")):
    for f in random.sample(pools[label], 20):
        dest = os.path.join(OUT, f"{prefix}_{f}")
        shutil.copy2(os.path.join(BASE, label, f), dest)
        labels[f"{prefix}_{f}"] = label

with open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8") as fp:
    json.dump(labels, fp, ensure_ascii=False, indent=2)

print(f"完成: 复制 {len(labels)} 条到 _ab40（真实 {sum(1 for v in labels.values() if v=='real')} / 伪造 {sum(1 for v in labels.values() if v=='fake')}）")
