# -*- coding: utf-8 -*-
"""40 条融合判定 v2：规则族 D = phys≥p2 ∨ (伪造票≥t1 ∧ 先验≥p1)。
粗网格 + 各阈值二分细化；排序键 = (总正确率, 检出-误报, 检出)。"""
import glob
import json
import os

labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_self40\labels.json", encoding="utf-8")).items()}

rows = []
for f in sorted(glob.glob(r"E:\deepfake\output_self40_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        votes = r.get("vote_result") or {}
        fv = sum(votes.get(k, 0) for k in ("换脸", "面部重演", "全生成"))
        rows.append({"name": r["task_name"], "label": labels.get(r["task_name"], "?"),
                     "fv": fv, "prior": r.get("prior_p") or 0,
                     "phys": r.get("phys_score") if r.get("phys_score") is not None else -9})

FAKE_N = sum(1 for r in rows if r["label"] == "fake")


def evaluate(t1, p1, p2):
    hit = miss = fp = ok = 0
    for r in rows:
        v = "伪造" if (r["phys"] >= p2 or (r["fv"] >= t1 and r["prior"] >= p1)) else "无伪造"
        if r["label"] == "fake":
            hit += (v == "伪造"); miss += (v == "无伪造")
        else:
            fp += (v == "伪造"); ok += (v == "无伪造")
    acc = (hit + ok) / len(rows)
    return (acc, hit - fp, hit, miss, fp)


print("===== 单信号基线 =====")
for tag, rule in [
    ("纯提示词票(≥2伪造票)", lambda r: "伪造" if r["fv"] >= 2 else "无伪造"),
    ("纯提示词票(≥1伪造票)", lambda r: "伪造" if r["fv"] >= 1 else "无伪造"),
    ("纯先验(≥0.55)", lambda r: "伪造" if r["prior"] >= 0.55 else "无伪造"),
    ("纯phys(≥-0.5)", lambda r: "伪造" if r["phys"] >= -0.5 else "无伪造"),
]:
    hit = sum(1 for r in rows if r["label"] == "fake" and rule(r) == "伪造")
    fp = sum(1 for r in rows if r["label"] == "real" and rule(r) == "伪造")
    ok = sum(1 for r in rows if r["label"] == "real" and rule(r) == "无伪造")
    print(f"{tag:<22} 检出{hit:>2}/20 误报{fp:>2}/20 总正确率{(hit+ok)/40*100:>5.1f}%")

# ---- 粗扫 ----
best = None
for t1 in (1, 2, 3):
    for p1 in (round(0.30 + i * 0.02, 2) for i in range(36)):
        for p2 in (round(-1.2 + i * 0.05, 2) for i in range(49)):
            m = evaluate(t1, p1, p2)
            if best is None or m[:3] > best[0][:3]:
                best = (m, (t1, p1, p2))

# ---- 二分细化 ----
(acc, diff, hit, miss, fp), (t1, p1, p2) = best
for axis in ("p1", "p2"):
    step = 0.01
    for _ in range(10):
        improved = False
        for d in (-step, step):
            q1, q2 = p1 + (d if axis == "p1" else 0), p2 + (d if axis == "p2" else 0)
            if not (0 <= q1 <= 1 and -1.5 <= q2 <= 1.5):
                continue
            m = evaluate(t1, q1, q2)
            if m[:3] > (acc, diff, hit):
                acc, diff, hit, miss, fp = m
                p1, p2 = q1, q2
                improved = True
        if not improved:
            break

print("\n===== 最优融合规则（提示词票 ∧ 先验，或 phys）=====")
print(f"phys≥{p2:.2f} ∨ (伪造票≥{t1} ∧ 先验≥{p1:.2f}) → 伪造")
print(f"检出 {hit}/20（{hit/FAKE_N*100:.0f}%） 误报 {fp}/20（{fp/20*100:.0f}%） "
      f"漏判 {miss} 总正确率 {acc*100:.1f}%")


def fused(r):
    return "伪造" if (r["phys"] >= p2 or (r["fv"] >= t1 and r["prior"] >= p1)) else "无伪造"


print("\n===== 40 条融合判定明细 =====")
print(f"{'视频':<8}{'标签':<5}{'伪造票':<6}{'先验':>6}{'phys':>7}  融合判定")
for r in sorted(rows, key=lambda x: (x["label"], x["name"])):
    v = fused(r)
    mark = "✓" if v == ("伪造" if r["label"] == "fake" else "无伪造") else "✗"
    print(f"  {r['name']:<8}{r['label']:<5}{r['fv']:<6}{r['prior']:>6.3f}{r['phys']:>+7.2f}  → {v} {mark}")

out = {"rule": {"fv": t1, "prior": p1, "phys": p2},
       "metrics": {"检出": hit, "误报": fp, "漏判": miss, "总正确率": round(acc, 4)},
       "rows": [{**r, "fused": fused(r)} for r in rows]}
with open(r"E:\deepfake\output_self40_fusion.json", "w", encoding="utf-8") as fp:
    json.dump(out, fp, ensure_ascii=False, indent=2)
print("\n已保存: output_self40_fusion.json")
