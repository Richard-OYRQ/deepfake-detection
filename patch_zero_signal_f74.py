# -*- coding: utf-8 -*-
"""后补算 F74 缺失的 phys_score 并回填结果 JSON（原文件备份 .bak）。
与 patch_zero_signal.py 同逻辑（v6：phys 已在 physical_evidence_score 内截断 ±3）。"""
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, r"E:\deepfake\src")
from preprocessor import (analyze_video, stable_prior_probability,  # noqa: E402
                          physical_evidence_score, table_prior_value)

NAME = "F74"

paths = {}
for lab in glob.glob(r"E:\deepfake\_self160_c*\labels.json"):
    for k in json.load(open(lab, encoding="utf-8")):
        paths[os.path.splitext(k)[0]] = os.path.join(os.path.dirname(lab), k)
assert NAME in paths, f"缺路径: {NAME}"

vp = paths[NAME]
print(f"===== {NAME} ({os.path.basename(os.path.dirname(vp))}) =====", flush=True)
pre = analyze_video(vp)
p = stable_prior_probability(vp, pre, fusion="max")
if p is not None:
    anchored = table_prior_value(vp)
    if anchored is not None and abs(anchored - p) > 0.15:
        print(f"  先验锚定: 实时{p:.3f} → 表值{anchored:.3f}", flush=True)
        p = anchored
phys = physical_evidence_score(pre)
print(f"  prior={p if p is None else round(p, 3)}  "
      f"phys={phys if phys is None else round(phys, 3)}  "
      f"verdict={pre.get('verdict')}", flush=True)

for f in glob.glob(r"E:\deepfake\output_self160_c*\results_*.json"):
    d = json.load(open(f, encoding="utf-8"))
    changed = False
    for r in d["results"]:
        if r.get("task_name") == NAME:
            if p is not None:
                r["prior_p"] = round(p, 3)
            if phys is not None:
                r["phys_score"] = round(phys, 3)
            changed = True
    if changed:
        if not os.path.exists(f + ".bak"):
            shutil.copy2(f, f + ".bak")
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(d, fp, ensure_ascii=False, indent=2)
        print(f"  已回填 {os.path.basename(f)}", flush=True)
print("完成。", flush=True)
