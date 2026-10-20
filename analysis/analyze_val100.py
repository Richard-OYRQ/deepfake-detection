# -*- coding: utf-8 -*-
"""最终验证结果分析：v5.7 基线 vs v5.8 在同一批 100 条视频上的配对对比。
按分布（videos 校准分布 / 外部评测分布）分别统计检出、误报、存疑，
并逐视频列出判决变化，标注 v5.8 三个改动的预期效应：
  a) highres_conflict_exempt=false → 高清高先验"无伪造"应转"存疑"（预期捞回漏检）
  b) prior_convict_backstop 0.70→0.55 → 先验0.55~0.70的伪造票应转"伪造"（预期提升检出）
  c) 其余（死参数清理）不应产生任何判决变化
"""
import glob
import json
import os
import sys

sys.path.insert(0, r"E:\deepfake")
from src.processor import _parse_verdict  # noqa: E402  (仅用于票型诊断)

labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_val100\labels.json", encoding="utf-8")).items()}


def load(dirname):
    f = sorted(glob.glob(rf"E:\deepfake\{dirname}\results_*.json"))[-1]
    return json.load(open(f, encoding="utf-8"))["results"]


def summarize(recs, name):
    stats = {}
    for r in recs:
        lab = labels.get(r["task_name"])
        if lab not in stats:
            stats[lab] = {"n": 0, "伪造": 0, "无伪造": 0, "存疑": 0}
        stats[lab]["n"] += 1
        v = r.get("final_verdict", "失败")
        stats[lab][v] = stats[lab].get(v, 0) + 1
    print(f"--- {name} ---")
    for lab in ("fake", "real"):
        s = stats[lab]
        print(f"  {lab:4} {s['n']:>3} 条: 伪造 {s['伪造']:>2} | 无伪造 {s['无伪造']:>2} | 存疑 {s['存疑']:>2}")
    return stats


def verdict_map(recs):
    return {r["task_name"]: r for r in recs}


base = load("output_v58base")
v58 = load("output_v58final")
print("=" * 64)
sb = summarize(base, "v5.7 基线（backstop 0.70 / 高清冲突豁免开）")
sv = summarize(v58, "v5.8（backstop 0.55 / 高清冲突豁免关 / 死参数清理）")

# 分布拆分：videos(V_) vs 外部(E_)
def split(recs):
    v, e = [], []
    for r in recs:
        (v if r["task_name"].startswith("V_") else e).append(r)
    return v, e

print()
print("=" * 64)
print("按分布拆分：")
for name, recs in (("videos校准分布(40条)", []), ("外部评测分布(60条)", [])):
    pass
vb, eb = split(base)
vv, ev = split(v58)
for dist_name, (b, v) in (("videos校准分布(40条)", (vb, vv)), ("外部评测分布(60条)", (eb, ev))):
    print(f"  [{dist_name}]")
    for cfg_name, recs in (("v5.7", b), ("v5.8", v)):
        fk = sum(1 for r in recs if labels[r["task_name"]] == "fake" and r.get("final_verdict") == "伪造")
        fp = sum(1 for r in recs if labels[r["task_name"]] == "real" and r.get("final_verdict") == "伪造")
        ms_fk = sum(1 for r in recs if labels[r["task_name"]] == "fake" and r.get("final_verdict") == "无伪造")
        sus = sum(1 for r in recs if r.get("final_verdict") == "存疑")
        print(f"    {cfg_name}: 伪造检出 {fk} | 真实误报 {fp} | 伪造漏判 {ms_fk} | 存疑 {sus}")

# 逐视频变化
print()
print("=" * 64)
print("逐视频判决变化（v5.7 → v5.8）：")
bm, vm = verdict_map(base), verdict_map(v58)
changed = 0
for t in sorted(bm):
    b, v = bm[t].get("final_verdict"), vm[t].get("final_verdict")
    if b != v:
        changed += 1
        lab = labels.get(t, "?")
        prior = vm[t].get("prior_p")
        hr = vm[t].get("highres")
        print(f"  [{lab:4}] {t:<40} {b} → {v}  (prior={prior}, highres={hr})")
print(f"共 {changed} 条变化")

# 归因检查
print()
print("=" * 64)
print("归因检查：")
conflict_on = sum(1 for t in bm
                  if labels.get(t) == "fake" and vm[t].get("highres")
                  and bm[t].get("final_verdict") == "无伪造"
                  and vm[t].get("final_verdict") == "存疑"
                  and (vm[t].get("prior_p") or 0) >= 0.55)
backstop_up = sum(1 for t in bm
                  if bm[t].get("final_verdict") in ("存疑",) and vm[t].get("final_verdict") == "伪造")
backstop_down = sum(1 for t in bm
                    if bm[t].get("final_verdict") == "伪造" and vm[t].get("final_verdict") != "伪造")
print(f"  ① 高清冲突豁免取消捞回的伪造漏检: {conflict_on} 条")
print(f"  ② backstop 0.55 新增定罪: {backstop_up} 条（其中误报 {sum(1 for t in bm if labels.get(t)=='real' and bm[t].get('final_verdict')=='存疑' and vm[t].get('final_verdict')=='伪造')} 条）")
print(f"  ③ backstop 0.70→0.55 导致定罪丢失: {backstop_down} 条（理论应为0）")
