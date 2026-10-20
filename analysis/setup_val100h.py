# -*- coding: utf-8 -*-
"""v5.9 实验选片：把最终验证中的外部高清原片（43条）复制到 _val100h，写 labels.json。"""
import glob
import json
import os
import shutil

VAL = r"E:\deepfake\_val100"
OUT = r"E:\deepfake\_val100h"

labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(os.path.join(VAL, "labels.json"), encoding="utf-8")).items()}
d = json.load(open(sorted(glob.glob(r"E:\deepfake\output_v58final\results_*.json"))[-1],
                 encoding="utf-8"))

picks = [r["task_name"] for r in d["results"]
         if r["task_name"].startswith("E_") and r.get("highres")]

os.makedirs(OUT, exist_ok=True)
labels_out = {}
for name in picks:
    shutil.copy2(os.path.join(VAL, name + ".mp4"), os.path.join(OUT, name + ".mp4"))
    labels_out[name] = labels[name]
with open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8") as fp:
    json.dump(labels_out, fp, ensure_ascii=False, indent=2)

fake_n = sum(1 for v in labels_out.values() if v == "fake")
real_n = sum(1 for v in labels_out.values() if v == "real")
print(f"复制 {len(picks)} 条（伪造 {fake_n} / 真实 {real_n}）→ _val100h")
