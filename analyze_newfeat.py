# -*- coding: utf-8 -*-
"""第四信号分离性检验：
1. 各新特征在边界集（漏判37 vs 误报17）上的 AUC——能否切开"双低伪造"与"高先验真实"
2. 各新特征在全留出集 160 条上的 AUC（fake vs real）
3. 分组分布（漏判/误报/检出伪造/正确真实）
4. 各特征单阈值在边界集上的最优正确率（指示性，乐观上限）
"""
import json

FEATS = ["lip_corr", "lip_lag", "has_lip", "ppg_snr", "ppg_freq", "ppg_band",
         "az_hf", "az_peak", "corner"]

d = json.load(open(r"E:\deepfake\output_newfeat_160.json", encoding="utf-8"))
rows = d["rows"]
by_name = {r["name"]: r for r in rows}
fusion = json.load(open(r"E:\deepfake\output_self160_fusion.json", encoding="utf-8"))
for r in fusion["rows"]:
    by_name[r["name"]]["fused"] = r["fused"]


def auc(scores, ys):
    """rank AUC；scores 中 None 剔除。"""
    pairs = [(s, y) for s, y in zip(scores, ys) if s is not None]
    if len(pairs) < 4 or len({y for _, y in pairs}) < 2:
        return None
    pairs.sort()
    ranks = {i: (s, y) for i, (s, y) in enumerate(pairs)}
    n_pos = sum(1 for _, y in pairs if y == 1)
    n_neg = len(pairs) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    rsum = sum(i for i, (_, y) in ranks.items() if y == 1)
    return (rsum - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def group_of(r):
    if r["label"] == "fake":
        return "漏判" if r["fused"] == "无伪造" else "检出伪造"
    return "误报" if r["fused"] == "伪造" else "正确真实"


miss = [r for r in rows if group_of(r) == "漏判"]
fp = [r for r in rows if group_of(r) == "误报"]
hit = [r for r in rows if group_of(r) == "检出伪造"]
ok = [r for r in rows if group_of(r) == "正确真实"]
print(f"分组: 漏判{len(miss)} 误报{len(fp)} 检出伪造{len(hit)} 正确真实{len(ok)}")

print("\n===== 新特征分组分布（均值）=====")
print(f"{'特征':<10}" + "".join(f"{g:>14}" for g in ("漏判", "误报", "检出伪造", "正确真实")))
for f in FEATS:
    vals = []
    for grp in (miss, fp, hit, ok):
        v = [r.get(f) for r in grp if r.get(f) is not None]
        vals.append(f"{sum(v)/len(v):.3f}" if v else "-")
    print(f"{f:<10}" + "".join(f"{v:>14}" for v in vals))

print("\n===== AUC（fake=1）=====")
print(f"{'特征':<10}{'边界集54条':>12}{'全留出160条':>14}")
boundary = miss + fp
for f in FEATS:
    a1 = auc([r.get(f) for r in boundary], [1 if r["label"] == "fake" else 0 for r in boundary])
    a2 = auc([r.get(f) for r in rows], [1 if r["label"] == "fake" else 0 for r in rows])
    s1 = f"{a1:.3f}" if a1 is not None else "-"
    s2 = f"{a2:.3f}" if a2 is not None else "-"
    print(f"{f:<10}{s1:>12}{s2:>14}")

print("\n===== 单特征最优阈值（边界集，指示性上限）=====")
for f in FEATS:
    pairs = [(r.get(f), 1 if r["label"] == "fake" else 0) for r in boundary
             if r.get(f) is not None]
    if len(pairs) < 8:
        continue
    best = None
    for th in sorted({p[0] for p in pairs}):
        acc = sum(1 for v, y in pairs if (v > th) == (y == 1)) / len(pairs)
        if best is None or acc > best[0]:
            best = (acc, th)
    print(f"{f:<10} 最优正确率 {best[0]*100:5.1f}% @ 阈值 {best[1]:.3f}（基线: 边界集全按融合规则 0%）")
