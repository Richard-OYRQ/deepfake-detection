# -*- coding: utf-8 -*-
"""40 条真伪融合判定：
信号1（提示词）：控方轮票型中"伪造类"票数（换脸/面部重演/全生成，0~3）
信号2（OpenCV）：先验分数 prior_p（0~1）、物理证据子分 phys_score
策略：规则融合 + 阈值二分逼近，目标 = 总正确率最高（同正确率下取检出更高、误报更低的）。"""
import glob
import json
import os

labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_self40\labels.json", encoding="utf-8")).items()}

rows = []
for f in sorted(glob.glob(r"E:\deepfake\output_self40_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        votes = r.get("vote_result") or {}
        fake_votes = sum(votes.get(k, 0) for k in ("换脸", "面部重演", "全生成"))
        rows.append({
            "name": r["task_name"], "label": labels.get(r["task_name"], "?"),
            "fake_votes": fake_votes, "total_votes": sum(votes.values()) or 0,
            "votes": votes,
            "prior": r.get("prior_p"), "phys": r.get("phys_score"),
            "conf": r.get("final_confidence"),
        })

print(f"装载 {len(rows)} 条\n")

def evaluate(rule, rows):
    """rule(row)->'伪造'|'无伪造'，返回指标。"""
    hit = miss = fp = ok = 0
    for r in rows:
        v = rule(r)
        if r["label"] == "fake":
            hit += (v == "伪造")
            miss += (v == "无伪造")
        else:
            fp += (v == "伪造")
            ok += (v == "无伪造")
    n = len(rows)
    acc = (hit + ok) / n
    return {"检出": hit, "漏判": miss, "误报": fp, "无伪造": ok,
            "总正确率": acc, "检出率": hit / 20 * 100, "误报率": fp / 20 * 100}

# ---- 单信号基线 ----
print("===== 单信号基线 =====")
for tag, rule in [
    ("纯提示词票(≥2伪造票)", lambda r: "伪造" if r["fake_votes"] >= 2 else "无伪造"),
    ("纯提示词票(≥1伪造票)", lambda r: "伪造" if r["fake_votes"] >= 1 else "无伪造"),
    ("纯先验(≥0.55)", lambda r: "伪造" if (r["prior"] or 0) >= 0.55 else "无伪造"),
]:
    m = evaluate(rule, rows)
    print(f"{tag:<22} 检出{m['检出']:>2}/20 误报{m['误报']:>2}/20 总正确率{m['总正确率']*100:.1f}%")

# ---- 规则融合 + 阈值二分逼近 ----
print("\n===== 融合策略：伪造票为主 + 先验修正 =====")

def fused(t_vote, t_prior):
    def rule(r):
        fv, pr = r["fake_votes"], r["prior"] or 0
        if fv >= t_vote:
            return "伪造"
        if fv >= 1 and pr >= t_prior:
            return "伪造"
        return "无伪造"
    return rule

# 二分搜索 t_vote ∈ {1,2,3} × t_prior ∈ [0,1]，先粗扫再二分细化
best = None
for tv in (1, 2, 3):
    lo, hi = 0.0, 1.0
    for _ in range(12):  # 二分细化
        mid = (lo + hi) / 2
        m1 = evaluate(fused(tv, mid), rows)
        m2 = evaluate(fused(tv, mid + 1e-6), rows)
        # 分数：总正确率优先；同正确率时 检出-误报 更大者优先
        def score(m):
            return (m["总正确率"], m["检出"] - m["误报"], m["检出"])
        s1, s2 = score(m1), score(m2)
        if s1 >= s2:
            hi = mid
            cur = m1
        else:
            lo = mid
            cur = m2
    if best is None or (cur["总正确率"], cur["检出"] - cur["误报"], cur["检出"]) > \
            (best[1]["总正确率"], best[1]["检出"] - best[1]["误报"], best[1]["检出"]):
        best = ((tv, round(hi, 3)), cur)

tv, tp = best[0]
m = best[1]
print(f"最优融合: 伪造票≥{tv} 判伪造；伪造票=1~{tv-1} 且先验≥{tp} 判伪造；其余无伪造")
print(f"  检出 {m['检出']}/20（{m['检出率']:.0f}%） 误报 {m['误报']}/20（{m['误报率']:.0f}%） "
      f"漏判 {m['漏判']} 总正确率 {m['总正确率']*100:.1f}%")

# ---- 输出 40 条逐条判定 ----
rule = fused(tv, tp)
print("\n===== 40 条融合判定明细 =====")
print(f"{'视频':<12}{'标签':<6}{'票型':<16}{'先验':>6}{'phys':>7}{'融合判定':<8}{'对错'}")
import statistics
for r in sorted(rows, key=lambda x: (x["label"], x["name"])):
    v = rule(r)
    ok_mark = "✓" if v == ("伪造" if r["label"] == "fake" else "无伪造") else "✗"
    votes_s = "/".join(f"{k}{r['votes'].get(k,0)}" for k in ("无伪造", "换脸", "面部重演", "全生成") if r["votes"].get(k))
    print(f"{r['name']:<12}{r['label']:<6}{votes_s:<16}"
          f"{(r['prior'] if r['prior'] is not None else -1):>6.3f}"
          f"{(r['phys'] if r['phys'] is not None else -9):>7.2f}{v:<8}{ok_mark}")

# 保存结果
out = {"thresholds": {"fake_votes": tv, "prior": tp}, "metrics": m,
       "rows": [{**r, "fused": rule(r)} for r in rows]}
with open(r"E:\deepfake\output_self40_fusion.json", "w", encoding="utf-8") as fp:
    json.dump(out, fp, ensure_ascii=False, indent=2)
print("\n结果已保存: output_self40_fusion.json")
