# -*- coding: utf-8 -*-
"""M1 第二步：去重与训练池构建。

规则：
1. 待鉴别/ 是 videos/ 中 F 文件的拷贝 → 整目录剔除；
2. _self160/ 是 videos/ 的 160 条子集拷贝（80真+80伪）→ 单独冻结为留出集，
   同名的 videos/ 文件从训练池剔除（防止留出泄漏进训练）；
3. 外部评测集 3058 条全部进入训练池；
4. 输出 data/训练池清单.csv、data/留出集清单.csv、data/去重说明.md。
"""
import csv
import os
from collections import Counter

BASE = r"E:\deepfake"
MANIFEST = os.path.join(BASE, "data", "数据清单.csv")

rows = []
with open(MANIFEST, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append(r)

by_name = {}
for r in rows:
    by_name.setdefault(r["文件名"], []).append(r)

# ---- 验证重叠结构 ----
src_sets = {}
for src in ("videos", "待鉴别", "_self160"):
    src_sets[src] = {r["文件名"] for r in rows if r["来源"] == src}
print("重叠验证：")
print(f"  videos ∩ 待鉴别 = {len(src_sets['videos'] & src_sets['待鉴别'])}")
print(f"  videos ∩ _self160 = {len(src_sets['videos'] & src_sets['_self160'])}")
print(f"  待鉴别 ∩ _self160 = {len(src_sets['待鉴别'] & src_sets['_self160'])}")

# ---- 执行去重规则 ----
holdout_names = src_sets["_self160"]            # 冻结留出（160）
external = [r for r in rows if r["来源"] == "外部_real"]
external += [r for r in rows if r["来源"] == "外部_fake"]

train = []
for r in rows:
    if r["来源"] == "videos":
        if r["文件名"] in holdout_names:
            continue                                 # 与留出集同名的剔除
        train.append(r)
    elif r["来源"] == "待鉴别":
        if r["文件名"] not in src_sets["videos"]:
            train.append(r)                          # 待鉴别独有的伪造样本保留
train += external                                    # 外部 3058 全部进训练池

holdout = [r for r in rows if r["来源"] == "_self160"]

FIELDS = ["来源", "文件名", "标签", "家族", "宽", "高", "分辨率档", "大小MB"]


def write(path, data):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(data)


write(os.path.join(BASE, "data", "训练池清单.csv"), train)
write(os.path.join(BASE, "data", "留出集清单.csv"), holdout)

doc = f"""# 去重说明（2026-10-31）

## 重叠结构（实测）
- videos/ 与 待鉴别/ 同名 {len(src_sets['videos'] & src_sets['待鉴别'])} 个（待鉴别是 videos 的 F 拷贝）
- videos/ 与 _self160/ 同名 {len(src_sets['videos'] & src_sets['_self160'])} 个（留出集是基准集的子集拷贝）

## 规则
1. 待鉴别/ 中与 videos/ 同名的拷贝剔除；待鉴别独有的伪造样本保留
2. _self160/ 冻结为留出集；同名的 videos/ 文件从训练池剔除
3. 外部评测集全部进训练池

## 结果
- 训练池：{len(train)} 条（自建 {len(train) - len(external)} + 外部 {len(external)}）
- 留出集：{len(holdout)} 条（冻结考试卷）
"""
with open(os.path.join(BASE, "data", "去重说明.md"), "w", encoding="utf-8") as f:
    f.write(doc)

print(f"\n训练池: {len(train)} 条（自建 {len(train) - len(external)} + 外部 {len(external)}）")
print(f"留出集: {len(holdout)} 条")
print(f"已写入: data/训练池清单.csv、data/留出集清单.csv、data/去重说明.md")
