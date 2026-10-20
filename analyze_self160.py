# -*- coding: utf-8 -*-
"""160 条留出集复测：规则冻结 = phys≥0.55 ∨ (伪造票≥3 ∧ 先验≥0.56)，不重调阈值。
对比对象：40 条拟合集成绩（检出16/20、误报2/20、总正确率85.0%）。"""
import glob
import json
import os

RULE = {"fv": 3, "prior": 0.56, "phys": 0.55}   # 冻结自 output_self40_fusion.json
PHYS_CLIP = 3.0   # v6：phys 载入时截断 ±3（与 src/preprocessor.py 的 PHYS_SCORE_CLIP 一致）
INDIVISIBLE = {"F12", "F15", "F22", "F23", "F26",
               "F73", "F87", "86"}   # 9 条不可分样本中落在 videos/ 的 8 条（F23 在拟合集）

# task_name 不带扩展名（与 fusion40_v2.py 一致），标签键需去 .mp4
labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_self160\labels.json", encoding="utf-8")).items()}


def wilson(hits, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = hits / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return c - h, c + h


rows = []
for f in sorted(glob.glob(r"E:\deepfake\output_self160_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        votes = r.get("vote_result") or {}
        fv = sum(votes.get(k, 0) for k in ("换脸", "面部重演", "全生成"))
        phys_raw = r.get("phys_score")
        rows.append({"name": r["task_name"], "label": labels.get(r["task_name"], "?"),
                     "fv": fv, "prior": r.get("prior_p"),        # None = 特征缺失
                     "phys": max(-PHYS_CLIP, min(PHYS_CLIP, phys_raw))
                     if phys_raw is not None else None})         # None = 特征缺失

missing = [k for k in labels if k not in {r["name"] for r in rows}]
assert not missing, f"缺结果: {missing}"
n_fake = sum(1 for r in rows if r["label"] == "fake")
n_real = sum(1 for r in rows if r["label"] == "real")
print(f"留出集载入: {len(rows)} 条（伪{n_fake} / 真{n_real}）")


def fused(r):
    if r["prior"] is None or r["phys"] is None:
        return "存疑"   # v6：特征缺失哨兵不得默认"无伪造"（此前 F63/F74/F88/F96 必漏）
    return "伪造" if (r["phys"] >= RULE["phys"]
                      or (r["fv"] >= RULE["fv"] and r["prior"] >= RULE["prior"])) else "无伪造"


hit = miss = fp = ok = sus = 0
for r in rows:
    v = fused(r)
    if r["label"] == "fake":
        hit += (v == "伪造"); miss += (v == "无伪造"); sus += (v == "存疑")
    else:
        fp += (v == "伪造"); ok += (v == "无伪造"); sus += (v == "存疑")
acc = (hit + ok) / len(rows)

print("\n===== 冻结规则复测（留出 160 条）=====")
print(f"规则: phys≥{RULE['phys']} ∨ (伪造票≥{RULE['fv']} ∧ 先验≥{RULE['prior']}) → 伪造")
print(f"检出 {hit}/{n_fake}（{hit/n_fake*100:.1f}% [{wilson(hit, n_fake)[0]*100:.1f}, {wilson(hit, n_fake)[1]*100:.1f}]）")
print(f"误报 {fp}/{n_real}（{fp/n_real*100:.1f}% [{wilson(fp, n_real)[0]*100:.1f}, {wilson(fp, n_real)[1]*100:.1f}]）")
print(f"漏判 {miss}  存疑 {sus}  总正确率 {acc*100:.1f}% [{wilson(hit+ok, len(rows))[0]*100:.1f}, {wilson(hit+ok, len(rows))[1]*100:.1f}]")
print("\n===== 与 40 条拟合集对比 =====")
print(f"拟合集: 检出16/20(80.0%) 误报2/20(10.0%) 总正确率85.0%")
print(f"留出集: 检出{hit}/{n_fake}({hit/n_fake*100:.1f}%) 误报{fp}/{n_real}({fp/n_real*100:.1f}%) 总正确率{acc*100:.1f}%")

def _fmt(x, spec, miss="   缺"):
    """None（特征缺失）的打印占位。"""
    return spec % x if x is not None else miss


def _mark(r, v):
    if v == "存疑":
        return "⚠"
    return "✓" if v == ("伪造" if r["label"] == "fake" else "无伪造") else "✗"


print("\n===== 不可分样本（新特征目标集）在留出集中的表现 =====")
print(f"{'视频':<8}{'标签':<5}{'伪造票':<6}{'先验':>6}{'phys':>7}  融合判定")
for r in sorted((x for x in rows if x["name"] in INDIVISIBLE), key=lambda x: x["name"]):
    v = fused(r)
    print(f"  {r['name']:<8}{r['label']:<5}{r['fv']:<6}{_fmt(r['prior'], '%6.3f', '   缺')}{_fmt(r['phys'], '%+7.2f', '    缺')}  → {v} {_mark(r, v)}")

print("\n===== 特征分布对比（拟合集 vs 留出集）=====")
fit_rows = json.load(open(r"E:\deepfake\output_self40_fusion.json", encoding="utf-8"))["rows"]
for tag, src in [("拟合40", fit_rows), ("留出160", rows)]:
    fv_avg = sum(r["fv"] for r in src) / len(src)
    pri_vals = [r["prior"] for r in src if r["prior"] is not None]
    pri_avg = sum(pri_vals) / len(pri_vals) if pri_vals else float("nan")
    phys_miss = sum(1 for r in src if r["phys"] in (None, -9))
    print(f"{tag}: 伪造票均{fv_avg:.2f} 先验均{pri_avg:.3f} phys缺失{phys_miss}")

n_phys = sum(1 for r in rows if r["phys"] is not None and r["phys"] >= RULE["phys"])
n_vote = sum(1 for r in rows if r["prior"] is not None
             and r["fv"] >= RULE["fv"] and r["prior"] >= RULE["prior"])
print(f"留出集命中通道: phys≥0.55 {n_phys} 条, (票≥3∧先验≥0.56) {n_vote} 条")

print("\n===== 160 条融合判定明细 =====")
print(f"{'视频':<8}{'标签':<5}{'伪造票':<6}{'先验':>6}{'phys':>7}  融合判定")
for r in sorted(rows, key=lambda x: (x["label"], x["name"])):
    v = fused(r)
    print(f"  {r['name']:<8}{r['label']:<5}{r['fv']:<6}{_fmt(r['prior'], '%6.3f', '   缺')}{_fmt(r['phys'], '%+7.2f', '    缺')}  → {v} {_mark(r, v)}")

out = {"rule": {**RULE, "phys_clip": PHYS_CLIP},
       "metrics": {"检出": hit, "误报": fp, "漏判": miss, "存疑": sus,
                   "总正确率": round(acc, 4)},
       "fit_metrics": {"检出": 16, "误报": 2, "漏判": 4, "总正确率": 0.85},
       # 输出沿用 0/-9 哨兵编码（下游 newfeat 脚本按数值读取），语义上缺失行 fused=存疑
       "rows": [{**r, "prior": r["prior"] if r["prior"] is not None else 0,
                 "phys": r["phys"] if r["phys"] is not None else -9,
                 "fused": fused(r)} for r in rows]}
with open(r"E:\deepfake\output_self160_fusion.json", "w", encoding="utf-8") as fp:
    json.dump(out, fp, ensure_ascii=False, indent=2)
print("\n已保存: output_self160_fusion.json")
