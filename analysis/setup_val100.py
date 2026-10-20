# -*- coding: utf-8 -*-
"""最终验证采样：videos 真/伪各20（排除exp6用过的6条）+ 外部评测集真/伪各30（排除_ab40与exp4用过的）。
复制到 _val100 并写 labels.json（标签仅用于结果分析，不参与检测）。"""
import json
import os
import random
import shutil

random.seed(20260927)
OUT = r"E:\deepfake\_val100"

# 已用文件
used = set()
for d in os.listdir(r"E:\deepfake"):
    if d.startswith("_exp4c") and os.path.isdir(os.path.join(r"E:\deepfake", d)):
        used.update(f for f in os.listdir(os.path.join(r"E:\deepfake", d))
                    if os.path.splitext(f)[1].lower() in {".mp4", ".avi", ".mov", ".mkv", ".webm"})
# _ab40 的复制件带 R_/F_ 前缀，还原原名
used.update(n.split("_", 1)[1] for n in os.listdir(r"E:\deepfake\_ab40")
            if n.startswith(("R_", "F_")))
# exp6 用过的 6 条伪造（来自 videos）
used.update(f"F{n}.mp4" for n in (6, 8, 18, 42, 45, 51))

VID_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
def vid_files(d):
    return [f for f in os.listdir(d)
            if os.path.splitext(f)[1].lower() in VID_EXT and os.path.isfile(os.path.join(d, f))]

# videos：纯数字=真实，F开头=伪造（用户约定）
vids = vid_files(r"E:\deepfake\videos")
v_real = [f for f in vids if f[0].isdigit() and f not in used]
v_fake = [f for f in vids if f.startswith("F") and f not in used]

# 外部评测集：real/ fake/ 目录即标签
ext_real = [f for f in vid_files(r"E:\deepfake\外部评测集100\real") if f not in used]
ext_fake = [f for f in vid_files(r"E:\deepfake\外部评测集100\fake") if f not in used]

os.makedirs(OUT, exist_ok=True)
labels = {}
plan = [("V_real", v_real, 20, r"E:\deepfake\videos", "real"),
        ("V_fake", v_fake, 20, r"E:\deepfake\videos", "fake"),
        ("E_real", ext_real, 30, r"E:\deepfake\外部评测集100\real", "real"),
        ("E_fake", ext_fake, 30, r"E:\deepfake\外部评测集100\fake", "fake")]
for prefix, pool, n, src, label in plan:
    picks = random.sample(pool, n)
    for f in picks:
        dest = os.path.join(OUT, f"{prefix}_{f}")
        shutil.copy2(os.path.join(src, f), dest)
        labels[f"{prefix}_{f}"] = label
    print(f"{prefix}: 池 {len(pool)} → 抽 {n}")

with open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8") as fp:
    json.dump(labels, fp, ensure_ascii=False, indent=2)
print(f"完成: 共 {len(labels)} 条 → _val100")
