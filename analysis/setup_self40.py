# -*- coding: utf-8 -*-
"""从 _self60 抽样中取前 20 真 + 前 20 伪，组成 _self40（8 批次，更快跑完）。"""
import json
import os
import shutil

SRC = r"E:\deepfake\_self60"
OUT = r"E:\deepfake\_self40"
os.makedirs(OUT, exist_ok=True)

labels = json.load(open(os.path.join(SRC, "labels.json"), encoding="utf-8"))
fakes = sorted(k for k, v in labels.items() if v == "fake")[:20]
reals = sorted(k for k, v in labels.items() if v == "real")[:20]

out_labels = {}
for f in fakes + reals:
    shutil.copy2(os.path.join(SRC, f), os.path.join(OUT, f))
    out_labels[f] = labels[f]
with open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8") as fp:
    json.dump(out_labels, fp, ensure_ascii=False, indent=2)
print(f"完成：{len(out_labels)} 条 → _self40（真实 {sum(1 for v in out_labels.values() if v=='real')} / "
      f"伪造 {sum(1 for v in out_labels.values() if v=='fake')}）")
