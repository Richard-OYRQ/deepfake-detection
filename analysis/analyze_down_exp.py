# -*- coding: utf-8 -*-
"""降分辨率对照实验分析：
同一批外部视频：原始高清（output_v58final 已跑） vs ffmpeg 降清副本（output_v58down）。
判决标准：
  - 若降清后伪造检出/存疑明显上升 → 分辨率是机制变量，但路由方向反了（该降清送检）
  - 若判决基本不变 → 分辨率与模型失明无关，路由前提 P2 倒塌，应废除分辨率路由
"""
import glob
import json
import os

labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_down_exp\labels.json", encoding="utf-8")).items()}

def load(dirname):
    f = sorted(glob.glob(rf"E:\deepfake\{dirname}\results_*.json"))[-1]
    return {r["task_name"]: r for r in json.load(open(f, encoding="utf-8"))["results"]}

orig = load("output_v58final")   # 原始高清（同批视频已在最终验证跑过）
down = load("output_v58down")    # 降清副本

# 汇总
agg = {"fake": {"orig": {}, "down": {}}, "real": {"orig": {}, "down": {}}}
def tally(recs):
    t = {"伪造": 0, "无伪造": 0, "存疑": 0, "失败": 0}
    for r in recs:
        t[r.get("final_verdict", "失败")] = t.get(r.get("final_verdict", "失败"), 0) + 1
    return t

print("=" * 66)
print(f"{'':<8}{'伪造检出':>8}{'漏判(无伪造)':>12}{'存疑':>6}{'误报(伪造)':>10}{'无伪造':>8}{'存疑':>6}")
for lab, cn in (("fake", "伪造"), ("real", "真实")):
    o = [orig[n] for n in labels if labels[n] == lab and n in orig]
    d = [down[n] for n in labels if labels[n] == lab and n in down]
    to, td = tally(o), tally(d)
    if lab == "fake":
        print(f"{cn:<8}{to['伪造']:>8}{to['无伪造']:>12}{to['存疑']:>6}  vs  "
              f"{td['伪造']:>8}{td['无伪造']:>12}{td['存疑']:>6}    <- 降清后")
    else:
        print(f"{cn:<8}{to['伪造']:>8}{'':>12}{to['存疑']:>6}  vs  "
              f"{td['伪造']:>8}{'':>12}{td['存疑']:>6}    <- 降清后")
print()

# 逐条变化
print("逐视频变化（高清 → 降清）：")
changed = 0
for n in sorted(labels):
    if n not in orig or n not in down:
        print(f"  [{labels[n]}] {n}: 缺数据")
        continue
    vo, vd = orig[n].get("final_verdict"), down[n].get("final_verdict")
    po, pd = orig[n].get("prior_p"), down[n].get("prior_p")
    if vo != vd:
        changed += 1
        print(f"  [{labels[n]:4}] {n:<44} {vo} → {vd}  (prior {po} → {pd})")
print(f"共 {changed} 条判决变化 / {len(labels)} 条")

# 先验漂移
import statistics
deltas_fake = [down[n].get("prior_p") - orig[n].get("prior_p") for n in labels
               if labels[n] == "fake" and n in orig and n in down
               and orig[n].get("prior_p") is not None and down[n].get("prior_p") is not None]
deltas_real = [down[n].get("prior_p") - orig[n].get("prior_p") for n in labels
               if labels[n] == "real" and n in orig and n in down
               and orig[n].get("prior_p") is not None and down[n].get("prior_p") is not None]
def fmt(xs):
    if not xs:
        return "n/a"
    return f"均值 {statistics.mean(xs):+.3f}  范围 [{min(xs):+.2f}, {max(xs):+.2f}]"
print()
print(f"先验漂移（降清后 - 原始高清）:")
print(f"  伪造 {len(deltas_fake)} 条: {fmt(deltas_fake)}")
print(f"  真实 {len(deltas_real)} 条: {fmt(deltas_real)}")
