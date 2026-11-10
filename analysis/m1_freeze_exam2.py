# -*- coding: utf-8 -*-
"""留出集调整③：第二张考试卷（跨家族泛化卷）。
- 外部 7 个伪造家族各切 5% + 外部真实切 5%（排除曾用作换脸素材的 60 条，
  避免"训练里的假视频与冻结考卷里的真视频同场景"的内容泄漏）
- 输出：data/第二考试卷清单.csv（冻结卷）+ 更新后的 data/训练池清单.csv"""
import csv
import os
import random
import re

BASE = r"E:\deepfake"
random.seed(20261101)

FAMILIES = ["FaceShifter", "Face2Face", "NeuralTextures", "Deepfakes",
            "DeepFakeDetection", "FaceSwap", "DF-VAE(DF1.0)"]

with open(os.path.join(BASE, "data", "训练池清单.csv"), encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

# 换脸素材中的外部真实名单（来源文件 NN_外部_real_<原名>）
swap_reals = set()
for fn in os.listdir(os.path.join(BASE, "_swap_source")):
    m = re.match(r"\d+_外部_real_(.+)\.\w+$", fn)
    if m:
        swap_reals.add(m.group(1))

frozen = []
pool = [r for r in rows]
# 伪造侧：7 家族各切 5%
for fam in FAMILIES:
    cand = [r for r in pool if r["来源"] == "外部_fake" and r["家族"] == fam]
    n = max(1, round(len(cand) * 0.05))
    picked = random.sample(cand, n)
    frozen += picked
    for p in picked:
        pool.remove(p)
    print(f"冻结 {fam}: {n}/{len(cand)}", flush=True)

# 真实侧：外部真实切 5%（排除换脸素材）
cand_real = [r for r in pool if r["来源"] == "外部_real"
             and r["文件名"] not in swap_reals]
n_real = round(len(cand_real) * 0.05)
picked_real = random.sample(cand_real, n_real)
frozen += picked_real
for p in picked_real:
    pool.remove(p)
print(f"冻结 外部真实: {n_real}/{len(cand_real)}（换脸素材 {len(swap_reals)} 条已排除）",
      flush=True)

FIELDS = ["来源", "文件名", "标签", "家族", "宽", "高", "分辨率档", "大小MB"]
with open(os.path.join(BASE, "data", "第二考试卷清单.csv"), "w", newline="",
          encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(frozen)
with open(os.path.join(BASE, "data", "训练池清单.csv"), "w", newline="",
          encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(pool)

print(f"\n冻结卷 {len(frozen)} 条，训练池剩余 {len(pool)} 条", flush=True)
