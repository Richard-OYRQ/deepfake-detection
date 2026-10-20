# -*- coding: utf-8 -*-
"""② CV 先验粗筛层离线验证：
规则候选：先验 < thr 的视频跳过 MLLM，直接判"无伪造"。
统计各阈值下漏网的伪造（代价）与被滤掉的视频数（省下的调用量）。
数据池：full200（200条）+ v511 批次（100条），标签按命名约定/目录映射。"""
import glob
import json
import os

def label_of(name):
    n = str(name)
    return "fake" if n.startswith("F") else ("real" if (n[0].isdigit() and not n.startswith("E_")) else None)

# ---- full200 ----
f200 = sorted(glob.glob(r"E:\deepfake\output_full200\results_*.json"))[-1]
pool = []
for r in json.load(open(f200, encoding="utf-8"))["results"]:
    lab = "fake" if r["task_name"].startswith("F") else "real"
    pool.append((r["task_name"], lab, r.get("prior_p"), "full200"))

# ---- v511 批次 ----
val_labels = {os.path.splitext(k)[0]: v for k, v in
              json.load(open(r"E:\deepfake\_val100\labels.json", encoding="utf-8")).items()}
for f in sorted(glob.glob(r"E:\deepfake\output_v511_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        n = r["task_name"][:-4] if r["task_name"].endswith(".mp4") else r["task_name"]
        pool.append((n, val_labels.get(n, "?"), r.get("prior_p"), "v511"))

with_prior = [(n, lab, p, src) for n, lab, p, src in pool if p is not None]
print(f"带先验样本: {len(with_prior)} 条（伪造 {sum(1 for x in with_prior if x[1]=='fake')} / 真实 {sum(1 for x in with_prior if x[1]=='real')}）\n")

print(f"{'阈值':<6}{'滤掉总数':>8}{'其中真实':>8}{'漏网伪造':>8}{'省调用占比':>10}")
for thr in (0.10, 0.15, 0.20, 0.25, 0.30):
    below = [x for x in with_prior if x[2] < thr]
    reals = sum(1 for x in below if x[1] == "real")
    fakes = [x for x in below if x[1] == "fake"]
    pct = len(below) / len(with_prior) * 100
    print(f"{thr:<6}{len(below):>8}{reals:>8}{len(fakes):>8}{pct:>9.0f}%")

print("\n各阈值漏网伪造明细（阈值0.20）：")
for n, lab, p, src in sorted([x for x in with_prior if x[1] == "fake" and x[2] < 0.20], key=lambda x: x[2]):
    print(f"  [{src}] {n:<45} prior={p:.3f}")

print("\n阈值0.25漏网伪造明细：")
for n, lab, p, src in sorted([x for x in with_prior if x[1] == "fake" and x[2] < 0.25], key=lambda x: x[2]):
    print(f"  [{src}] {n:<45} prior={p:.3f}")
