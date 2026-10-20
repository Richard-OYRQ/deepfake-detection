# -*- coding: utf-8 -*-
"""第3项离线模拟：检察官轮一致伪造票 + 证据子分门槛 → 定罪，回放 160 条已有结果。
不改任何结果文件，只统计"存疑→伪造"的翻转及真假分布。

规则变体：
  A  检察官轮 fv==3 ∧ evidence≥4 ∧ conf≥85            （建议版）
  A' A 且 prior≥0.55（保留 backstop）
  B  fv==3 ∧ evidence≥3 ∧ conf≥85                    （证据门槛放宽）
  C  A + 平票处理（fv==2 ∧ evidence≥4 ∧ conf≥85）     （含 F99 型两伪造票）
"""
import glob
import json
import os

labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_self160\labels.json", encoding="utf-8")).items()}

rows = []
for f in sorted(glob.glob(r"E:\deepfake\output_self160_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        votes = r.get("vote_result") or {}
        fv = sum(votes.get(k, 0) for k in ("换脸", "面部重演", "全生成"))
        rows.append({
            "name": r["task_name"], "label": labels.get(r["task_name"], "?"),
            "fv": fv, "verdict": r.get("final_verdict"),
            "conf": r.get("final_confidence") or 0,
            "ev": r.get("evidence_score") or 0,
            "prior": r.get("prior_p"), "phys": r.get("phys_score"),
        })

# 基线：当前管线终裁（非融合规则）
base_hit = sum(1 for r in rows if r["label"] == "fake" and r["verdict"] == "伪造")
base_fp = sum(1 for r in rows if r["label"] == "real" and r["verdict"] == "伪造")
base_sus_fake = sum(1 for r in rows if r["label"] == "fake" and r["verdict"] == "存疑")
base_sus_real = sum(1 for r in rows if r["label"] == "real" and r["verdict"] == "存疑")
print(f"基线（当前管线终裁）: 硬检出 {base_hit}/80  误报 {base_fp}/80  "
      f"存疑: 伪{base_sus_fake} 真{base_sus_real}  其余无伪造")


def flip(cond, tag):
    """按条件把 存疑 翻为 伪造，统计翻转明细。"""
    gained, fp_new, names = [], [], []
    for r in rows:
        if r["verdict"] == "存疑" and cond(r):
            (gained if r["label"] == "fake" else fp_new).append(r)
    print(f"\n----- 变体 {tag}: 存疑→伪造 共 {len(gained) + len(fp_new)} 条 "
          f"（伪 {len(gained)} / 真 {len(fp_new)}）-----")
    if gained:
        print("  新检出:", ", ".join(
            f"{r['name']}(fv{r['fv']} ev{r['ev']} conf{r['conf']} pri{r['prior']:.2f})"
            for r in gained))
    if fp_new:
        print("  新误报:", ", ".join(
            f"{r['name']}(fv{r['fv']} ev{r['ev']} conf{r['conf']} pri{r['prior']:.2f})"
            for r in fp_new))
    hit = base_hit + len(gained)
    fp = base_fp + len(fp_new)
    acc = (hit + (80 - fp)) / 160
    print(f"  → 硬检出 {hit}/80 ({hit/80*100:.1f}%)  误报 {fp}/80 ({fp/80*100:.1f}%)  "
          f"终裁正确率 {acc*100:.1f}%")


flip(lambda r: r["fv"] == 3 and r["ev"] >= 4 and r["conf"] >= 85, "A  fv3∧ev≥4∧conf≥85")
flip(lambda r: r["fv"] == 3 and r["ev"] >= 4 and r["conf"] >= 85
     and r["prior"] is not None and r["prior"] >= 0.55, "A' A∧prior≥0.55")
flip(lambda r: r["fv"] == 3 and r["ev"] >= 3 and r["conf"] >= 85, "B  fv3∧ev≥3∧conf≥85")
flip(lambda r: r["fv"] >= 2 and r["ev"] >= 4 and r["conf"] >= 85, "C  fv≥2∧ev≥4∧conf≥85")

# 变体 A 翻转样本的对照：未翻转的 fv==3 存疑伪造长什么样
print("\n===== 对照：fv==3 但仍存疑/无伪造的伪造样本（变体 A 漏掉的）=====")
for r in sorted((x for x in rows if x["label"] == "fake" and x["fv"] == 3
                 and x["verdict"] in ("存疑", "无伪造")), key=lambda x: -x["ev"]):
    print(f"  {r['name']:<6} verdict={r['verdict']:<4} ev={r['ev']} conf={r['conf']} "
          f"pri={r['prior'] if r['prior'] is not None else '缺':>4} "
          f"phys={r['phys'] if r['phys'] is not None else '缺'}")
