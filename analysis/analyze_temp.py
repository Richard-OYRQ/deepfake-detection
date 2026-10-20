# -*- coding: utf-8 -*-
"""④ 温度分层分析：9 条边界样本，复检温度 0.7（v511首跑）vs 0.05（v512temp）。
对比票型分裂率与修正版终裁。"""
import glob
import json
import os
import sys

sys.path.insert(0, r"E:\deepfake")
from src.config import AppConfig
from src.processor import VideoProcessor

labels = {k: v for k, v in
          json.load(open(r"E:\deepfake\_bound9\labels.json", encoding="utf-8")).items()}


def load_v511():
    out = {}
    for f in sorted(glob.glob(r"E:\deepfake\output_v511_c*\results_*.json")):
        for r in json.load(open(f, encoding="utf-8"))["results"]:
            n = r["task_name"][:-4] if r["task_name"].endswith(".mp4") else r["task_name"]
            out[n] = r
    return out


def load_temp():
    f = sorted(glob.glob(r"E:\deepfake\output_v512temp\results_*.json"))[-1]
    return {r["task_name"]: r for r in json.load(open(f, encoding="utf-8"))["results"]}


v511 = load_v511()
temp = load_temp()

# 边界9条在 v511 中的名字映射（V_fake_F12 -> F12.mp4 等）
def v511_key(n):
    for k in v511:
        if k.endswith(n[:-4]) or k == n[:-4]:
            return k
    return None

cfg = AppConfig.from_yaml(r"E:\deepfake\config_v511.yaml")
proc = VideoProcessor(cfg, None, None)

print(f"{'样本':<32}{'标签':<5}{'0.7票型':<28}{'0.05票型':<28}{'0.7终裁':<8}{'0.05终裁'}")
for n in sorted(labels):
    stem = n[:-4]
    k = v511_key(n)
    r07 = v511.get(k)
    r05 = temp.get(stem)
    if r07 is None or r05 is None:
        print(f"{n:<32} 缺数据 (v511={k}, temp={stem})")
        continue

    t07 = r07.get("vote_result") or {}
    t05 = r05.get("vote_result") or {}
    s07 = "分裂" if len(t07) > 1 else ("无伪造" if "无伪造" in t07 else ("伪造" if any(x in t07 for x in ("换脸", "面部重演", "全生成")) else "?"))
    s05 = "分裂" if len(t05) > 1 else ("无伪造" if "无伪造" in t05 else ("伪造" if any(x in t05 for x in ("换脸", "面部重演", "全生成")) else "?"))

    for r, tag in ((r07, "07"), (r05, "05")):
        rr = dict(r)
        proc._finalize_result(rr, prior_p=r.get("prior_p"), phys_score=r.get("phys_score"),
                              highres=r.get("highres", False))
        r[tag + "_v"] = rr.get("final_verdict")

    print(f"{n:<32}{labels[n]:<5}{str(t07):<28}{str(t05):<28}{r07['07_v']:<8}{r05['05_v']}")

# 汇总
def count(recs):
    split = sum(1 for r in recs if len(r.get("vote_result") or {}) > 1)
    return split, len(recs) - split
s07, u07 = count([v511[k] for k in v511 if v511_key(k)])
s05, u05 = count([temp[n[:-4]] for n in labels])
print(f"\n票型分裂: 0.7温度 {s07}/{s07+u07} vs 0.05温度 {s05}/{s05+u05}")
