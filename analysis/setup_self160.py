# -*- coding: utf-8 -*-
"""留出集 _self160：videos/ 200 条扣除拟合集 _self40 的 40 条 → 80 真实 + 80 伪造。
标签由命名约定直接生成（F开头=伪造，纯数字=真实），严禁流入检测流程。"""
import json
import os
import shutil

SRC = r"E:\deepfake\videos"
FIT = r"E:\deepfake\_self40"
DST = r"E:\deepfake\_self160"

fit = set(json.load(open(os.path.join(FIT, "labels.json"), encoding="utf-8")).keys())
files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp4"))
held = [f for f in files if f not in fit]

labels = {}
for f in held:
    base = os.path.splitext(f)[0]
    if base.startswith("F"):
        labels[f] = "fake"
    elif base.isdigit():
        labels[f] = "real"
    else:
        raise SystemExit(f"命名不符合约定，拒绝入集: {f}")

assert len(held) == 160, f"期望160，实际{len(held)}"
assert sum(v == "fake" for v in labels.values()) == 80
assert sum(v == "real" for v in labels.values()) == 80
assert not (fit & set(held)), f"与拟合集重叠: {fit & set(held)}"

os.makedirs(DST, exist_ok=True)
with open(os.path.join(DST, "labels.json"), "w", encoding="utf-8") as fp:
    json.dump(labels, fp, ensure_ascii=False, indent=2)

for f in held:
    src, dest = os.path.join(SRC, f), os.path.join(DST, f)
    if not os.path.exists(dest) or os.path.getsize(dest) != os.path.getsize(src):
        shutil.copy2(src, dest)

print(f"留出集: {len(held)} 条（伪{sum(1 for v in labels.values() if v == 'fake')} / "
      f"真{sum(1 for v in labels.values() if v == 'real')}），已写入 {DST}")
print("与拟合集重叠: 0")
