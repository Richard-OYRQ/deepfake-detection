# -*- coding: utf-8 -*-
"""修复后补算 6 条零信号视频的 prior_p/phys_score 并回填结果 JSON（原文件备份 .bak）。
复刻 processor.py 注入逻辑：analyze_video → stable_prior_probability(fusion=max)
→ 先验锚定表 → physical_evidence_score。LLM 票型与终裁保持不变。"""
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, r"E:\deepfake\src")
from preprocessor import (analyze_video, stable_prior_probability,  # noqa: E402
                          physical_evidence_score, table_prior_value)

NAMES = ["63", "88", "96", "F63", "F88", "F96"]

# 视频名 → chunk 副本路径（从 _self160_cN/labels.json 定位）
paths = {}
for lab in glob.glob(r"E:\deepfake\_self160_c*\labels.json"):
    for k in json.load(open(lab, encoding="utf-8")):
        paths[os.path.splitext(k)[0]] = os.path.join(os.path.dirname(lab), k)
assert all(n in paths for n in NAMES), f"缺路径: {[n for n in NAMES if n not in paths]}"

for name in NAMES:
    vp = paths[name]
    print(f"===== {name} ({os.path.basename(os.path.dirname(vp))}) =====", flush=True)
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
            if r.get("task_name") == name:
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
print("全部完成。", flush=True)
