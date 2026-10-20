# -*- coding: utf-8 -*-
"""v5.9 实验分析：同一批 43 条外部高清原片的五方对比
  v5.7 (output_v58base)    : 高清单票快速通道（旧路由）
  v5.8 (output_v58final)   : + 取消冲突豁免（今天上午定稿）
  v59a (output_v59a)       : + 高清 3 票复检 + 守卫取消豁免（无 CV 图）
  v59b (output_v59b)       : v59a + 高清附加 CV 可视化证据图
  降清参考 (output_v58down) : 同批视频 ffmpeg 降清走低清分支（昨天实验）
两个变量的净贡献：复检 = v59a - v5.8；CV图 = v59b - v59a。
"""
import glob
import json
import os

labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(r"E:\deepfake\_val100h\labels.json", encoding="utf-8")).items()}


def load(dirs):
    """支持分批输出目录合并（内存受限时拆批跑，结果按 task_name 合并）。"""
    merged = {}
    for dirname in dirs:
        f = sorted(glob.glob(rf"E:\deepfake\{dirname}\results_*.json"))[-1]
        for r in json.load(open(f, encoding="utf-8"))["results"]:
            merged[r["task_name"]] = r
    return merged


def tally(recs, lab):
    t = {"伪造": 0, "无伪造": 0, "存疑": 0, "失败": 0}
    for n, r in recs.items():
        if labels.get(n) == lab:
            v = r.get("final_verdict", "失败")
            t[v] = t.get(v, 0) + 1
    return t


runs = [("v5.7 快速通道", load(["output_v58base"])),
        ("v5.8 取消冲突豁免", load(["output_v58final"])),
        ("v59a +高清复检", load(["output_v59a_fake", "output_v59a_real"])),
        ("v59b +CV证据图", load(["output_v59b_fake", "output_v59b_real"])),
        ("v59c +控方提示词", load(sorted(os.path.basename(p) for p in glob.glob(r"E:\deepfake\output_v59c_c*")))),
        ("降清参考(低清分支)", load(["output_v58down"]))]

print(f"{'':<20}{'伪造 检出/漏判/存疑':<24}{'真实 误报/无伪造/存疑':<24}")
for name, recs in runs:
    fk = tally(recs, "fake")
    rl = tally(recs, "real")
    print(f"{name:<20}{fk['伪造']:>3}/{fk['无伪造']:>2}/{fk['存疑']:>2}"
          f"{rl['伪造']:>10}/{rl['无伪造']:>3}/{rl['存疑']:>2}")

# 变量净贡献
print()
print("=== 变量净贡献（相对 v5.8）===")
v58 = load(["output_v58final"])
v59a = load(["output_v59a_fake", "output_v59a_real"])
v59b = load(["output_v59b_fake", "output_v59b_real"])

def diff(base, new, lab, verdict):
    return [n for n in labels if labels[n] == lab and n in base and n in new
            and base[n].get("final_verdict") == verdict
            and new[n].get("final_verdict") != verdict]

print("复检带来的变化（v59a vs v5.8）：")
for n in sorted(set(labels)):
    if n not in v58 or n not in v59a:
        continue
    o, a = v58[n].get("final_verdict"), v59a[n].get("final_verdict")
    if o != a:
        print(f"  [{labels[n]:4}] {n:<44} {o} → {a}  (prior={v59a[n].get('prior_p')})")

print()
print("CV证据图带来的变化（v59b vs v59a）：")
for n in sorted(set(labels)):
    if n not in v59a or n not in v59b:
        continue
    a, b = v59a[n].get("final_verdict"), v59b[n].get("final_verdict")
    if a != b:
        print(f"  [{labels[n]:4}] {n:<44} {a} → {b}  (prior={v59b[n].get('prior_p')})")
