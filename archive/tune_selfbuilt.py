# -*- coding: utf-8 -*-
"""自建集离线盘点与参数调优：
数据池 A：full200（自建 200 条历史结果，有 prior/conf/verdict，无票型——重放阈值类规则）
数据池 B：v511 的 V_ 子集（自建 40 条，有完整票型——全规则重放）
按零误报约束扫描冲突阈值×真实置信度门槛，找自建分布的最优配置。"""
import glob
import json
import os
import sys

sys.path.insert(0, r"E:\deepfake")
from src.config import AppConfig
from src.processor import VideoProcessor

# ---- 数据池 A：full200（标签按命名约定）----
pool_a = []
f = sorted(glob.glob(r"E:\deepfake\output_full200\results_*.json"))[-1]
for r in json.load(open(f, encoding="utf-8"))["results"]:
    lab = "fake" if r["task_name"].startswith("F") else "real"
    pool_a.append((r["task_name"], lab, r))

# ---- 数据池 B：v511 V_ 子集 ----
pool_b = []
val_labels = {os.path.splitext(k)[0]: v for k, v in
              json.load(open(r"E:\deepfake\_val100\labels.json", encoding="utf-8")).items()}
for f in sorted(glob.glob(r"E:\deepfake\output_v511_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        n = r["task_name"][:-4] if r["task_name"].endswith(".mp4") else r["task_name"]
        if n.startswith("V_"):
            pool_b.append((n, val_labels.get(n, "?"), r))


def replay(records, **patches):
    cfg = AppConfig.from_yaml(r"E:\deepfake\config_v511.yaml")
    for k, v in patches.items():
        setattr(cfg, k, v)
    proc = VideoProcessor(cfg, None, None)
    out = []
    for name, lab, r in records:
        rr = dict(r)
        proc._finalize_result(rr, prior_p=r.get("prior_p"), phys_score=r.get("phys_score"),
                              highres=r.get("highres", False))
        out.append((name, lab, rr))
    return out


def tally(records):
    t = {}
    for name, lab, r in records:
        t.setdefault(lab, {}).setdefault(r.get("final_verdict"), 0)
        t[lab][r.get("final_verdict")] += 1
    return t


def show(tag, records):
    t = tally(records)
    fk, rl = t.get("fake", {}), t.get("real", {})
    print(f"{tag:<44} 伪造 检出{fk.get('伪造',0)}/漏判{fk.get('无伪造',0)}/存疑{fk.get('存疑',0)}"
          f" | 真实 误报{rl.get('伪造',0)}/无伪造{rl.get('无伪造',0)}/存疑{rl.get('存疑',0)}")


print("===== 数据池A：full200 自建200条（阈值类规则可重放）=====")
show("基线(修正版代码, 冲突0.55/真90)", replay(pool_a))
print("参数扫描（零误报约束）：")
for conflict in (0.45, 0.50, 0.60):
    show(f"冲突阈值 {conflict}", replay(pool_a, prior_conflict_threshold=conflict))
for rc in (85, 95):
    show(f"真实置信度门槛 {rc}", replay(pool_a, final_real_conf_threshold=rc))
show("冲突0.45+真95 组合", replay(pool_a, prior_conflict_threshold=0.45, final_real_conf_threshold=95))

print()
print("===== 数据池B：v511 自建40条（全规则重放）=====")
show("基线(修正版)", replay(pool_b))
show("冲突0.45", replay(pool_b, prior_conflict_threshold=0.45))
show("冲突0.45+真95", replay(pool_b, prior_conflict_threshold=0.45, final_real_conf_threshold=95))
show("冲突0.45+真85", replay(pool_b, prior_conflict_threshold=0.45, final_real_conf_threshold=85))
