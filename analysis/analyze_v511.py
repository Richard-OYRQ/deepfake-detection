# -*- coding: utf-8 -*-
"""v5.11 回归分析：100 条同批视频上 v5.8 vs v5.11 对比。
v5.11 = 统一流程（控方复检全员化+守卫全员化+CV证据图全员化+融合规则清理）。
预期：低清视频行为与 v5.8 一致（噪声级差异）；高清视频达到 v59c 水平
（伪造近零漏判、真实大量存疑、零硬误报）。"""
import glob
import json
import os
import sys

sys.path.insert(0, r"E:\deepfake")
labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_val100\labels.json", encoding="utf-8")).items()}


def norm(name):
    """归一化 task_name：去掉可能残留的 .mp4 后缀（批驱动双扩展名乌龙所致）。"""
    return name[:-4] if name.endswith(".mp4") else name


def load(dirs):
    merged = {}
    for dirname in dirs:
        fs = glob.glob(rf"E:\deepfake\{dirname}\results_*.json")
        if not fs:
            continue
        for r in json.load(open(sorted(fs)[-1], encoding="utf-8"))["results"]:
            merged[norm(r["task_name"])] = r
    return merged


def tally(recs, lab):
    t = {"伪造": 0, "无伪造": 0, "存疑": 0, "失败": 0}
    for n, r in recs.items():
        if labels.get(n) == lab:
            v = r.get("final_verdict", "失败")
            t[v] = t.get(v, 0) + 1
    return t


v58 = load(["output_v58final"])
v511 = load(sorted(os.path.basename(p) for p in glob.glob(r"E:\deepfake\output_v511_c*")))

print(f"{'':<16}{'伪造 检出/漏判/存疑':<22}{'真实 误报/无伪造/存疑':<22}")
for name, recs in (("v5.8 基线", v58), ("v5.11 统一流程", v511)):
    fk, rl = tally(recs, "fake"), tally(recs, "real")
    print(f"{name:<16}{fk['伪造']:>3}/{fk['无伪造']:>3}/{fk['存疑']:>3}"
          f"{rl['伪造']:>8}/{rl['无伪造']:>4}/{rl['存疑']:>3}")

# 按分辨率拆分 v5.11（验证统一流程在各分辨率下的表现）
print("\nv5.11 按分辨率拆分：")
for hr, lab_name in ((True, "高清"), (False, "低清")):
    sub = {n: r for n, r in v511.items() if bool(r.get("highres")) == hr}
    fk, rl = tally(sub, "fake"), tally(sub, "real")
    print(f"  {lab_name}: 伪造 {fk['伪造']}/{fk['无伪造']}/{fk['存疑']}  "
          f"真实 {rl['伪造']}/{rl['无伪造']}/{rl['存疑']}")

# 逐视频变化
print("\n逐视频变化（v5.8 → v5.11）：")
changed = 0
for n in sorted(labels):
    if n not in v58 or n not in v511:
        continue
    o, v = v58[n].get("final_verdict"), v511[n].get("final_verdict")
    if o != v:
        changed += 1
        print(f"  [{labels[n]:4}] {n:<40} {o} → {v}  (prior={v511[n].get('prior_p')}, highres={v511[n].get('highres')})")
print(f"共 {changed} 条变化")

# phys_score 落盘检查
with_phys = sum(1 for r in v511.values() if r.get("phys_score") is not None)
print(f"\nphys_score 落盘: {with_phys}/{len(v511)}")
