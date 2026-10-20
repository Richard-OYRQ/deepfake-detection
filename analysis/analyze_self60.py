# -*- coding: utf-8 -*-
"""自建 40 条最新策略检测分析：双口径成绩单（15:00 汇报用）。"""
import glob
import json
import os
import sys

sys.path.insert(0, r"E:\deepfake")
labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_self40\labels.json", encoding="utf-8")).items()}

results = {}
for f in sorted(glob.glob(r"E:\deepfake\output_self40_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        results[r["task_name"]] = r

print(f"装载 {len(results)}/40 条结果\n")

t = {}
for n, r in results.items():
    lab = labels.get(n, "?")
    t.setdefault(lab, {}).setdefault(r.get("final_verdict", "失败"), 0)
    t[lab][r.get("final_verdict", "失败")] += 1

fk, rl = t.get("fake", {}), t.get("real", {})
hit, miss, sus_f = fk.get("伪造", 0), fk.get("无伪造", 0), fk.get("存疑", 0)
fp, ok, sus_r = rl.get("伪造", 0), rl.get("无伪造", 0), rl.get("存疑", 0)
total = len(results)
correct = hit + ok
susp = sus_f + sus_r

print("=== 自建 40 条最新策略成绩单（v5.11 修正版）===")
print(f"伪造 20: 检出 {hit} | 漏判 {miss} | 存疑 {sus_f}")
print(f"真实 20: 误报 {fp} | 无伪造 {ok} | 存疑 {sus_r}")
print()
print(f"综合正确率（存疑不计错）: {(correct + susp) / total * 100:.1f}%")
print(f"标准准确率（存疑计错）: {correct / total * 100:.1f}%")
print(f"检出率: {hit / 20 * 100:.1f}% | 误报率: {fp / 20 * 100:.1f}% | "
      f"漏判率: {miss / 20 * 100:.1f}% | 存疑率: {susp / total * 100:.1f}%")

print("\n漏判清单:", [n for n, r in results.items()
                    if labels.get(n) == 'fake' and r.get('final_verdict') == '无伪造'])
print("误报清单:", [n for n, r in results.items()
                    if labels.get(n) == 'real' and r.get('final_verdict') == '伪造'])
