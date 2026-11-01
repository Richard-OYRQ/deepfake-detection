# -*- coding: utf-8 -*-
"""M1 分层划分：按（标签, 家族）分组，组内随机 7:1.5:1.5 划分。
保证每个伪造家族在训练/验证/测试三份里都有样本。输出 data/划分结果.csv。"""
import csv
import os
import random

BASE = r"E:\deepfake"
random.seed(20261101)

with open(os.path.join(BASE, "data", "训练池清单.csv"), encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

groups = {}
for r in rows:
    key = (r["标签"], r["家族"])
    groups.setdefault(key, []).append(r)

train, val, test = [], [], []
for key, g in groups.items():
    random.shuffle(g)
    n = len(g)
    n_test = max(1, round(n * 0.15))
    n_val = max(1, round(n * 0.15))
    n_train = n - n_test - n_val
    test += [{**r, "划分": "test"} for r in g[:n_test]]
    val += [{**r, "划分": "val"} for r in g[n_test:n_test + n_val]]
    train += [{**r, "划分": "train"} for r in g[n_test + n_val:]]

FIELDS = ["来源", "文件名", "标签", "家族", "宽", "高", "分辨率档", "大小MB", "划分"]
out = train + val + test
with open(os.path.join(BASE, "data", "划分结果.csv"), "w", newline="",
          encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(out)

print(f"划分完成：训练 {len(train)} / 验证 {len(val)} / 测试 {len(test)}")
print()
print("--- 各家族在三份中的分布 ---")
print(f"{'家族':<22}{'训练':>6}{'验证':>6}{'测试':>6}")
from collections import Counter
fams = sorted({r["家族"] for r in out})
for fam in fams:
    c = Counter(r["划分"] for r in out if r["家族"] == fam)
    print(f"{fam:<22}{c.get('train',0):>6}{c.get('val',0):>6}{c.get('test',0):>6}")
