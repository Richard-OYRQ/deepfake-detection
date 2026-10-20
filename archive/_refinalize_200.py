# -*- coding: utf-8 -*-
"""离线重算终裁：8/23 全量运行 + 新融合先验表 → 三分类 & 全自动模式混淆矩阵。"""
import csv
import copy
import json
import os
import sys

sys.path.insert(0, r'D:\deepfake')

from reapply_fusion import refinalize

BASE = r'D:\deepfake'
SRC = os.path.join(BASE, 'output', 'results_2026-08-23T09-12-51Z_refused.json')

# 真值标签（融合先验表带 label）
labels = {}
with open(os.path.join(BASE, 'output', 'stable_prior_table.csv'), encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        labels[row['video'].rsplit('.', 1)[0]] = row['label']


def report(results, title):
    matrix = {'real': {}, 'fake': {}}
    for r in results:
        lb = labels.get(r.get('task_name'), '?')
        if lb not in matrix:
            continue
        v = r.get('final_verdict', '?')
        matrix[lb][v] = matrix[lb].get(v, 0) + 1
    print(f'===== {title} =====')
    print(f'  真实组(100): {matrix["real"]}')
    print(f'  伪造组(100): {matrix["fake"]}')
    tp = matrix['fake'].get('伪造', 0)
    fn = matrix['fake'].get('无伪造', 0)
    fp = matrix['real'].get('伪造', 0)
    tn = matrix['real'].get('无伪造', 0)
    sus = sum(matrix[lb].get('存疑', 0) for lb in ('real', 'fake'))
    hard_acc = (tp + tn) / 200 * 100
    print(f'  硬检出={tp}%  硬漏检={fn}%  硬误报={fp}%  硬正确={tn}%  存疑={sus}%  明确判定正确率={hard_acc:.1f}%')
    print()


with open(SRC, encoding='utf-8') as f:
    data = json.load(f)

old_matrix = {}
for r in data['results']:
    old_matrix[r.get('task_name')] = r.get('final_verdict')

# ---- 三分类模式 ----
triage = copy.deepcopy(data['results'])
for r in triage:
    refinalize(r, auto=False)
report(triage, '三分类模式（新融合先验，convict≥0.70 / 冲突≥0.55）')

# ---- 全自动模式 0.55 / 0.60 ----
for thr in (0.55, 0.60):
    auto = copy.deepcopy(data['results'])
    for r in auto:
        refinalize(r, auto=True, prior_fake_thr=thr, prior_real_thr=0.45)
    report(auto, f'全自动模式（先验≥{thr}→伪造，<0.45→无伪造，边界带模型票）')

# ---- 变化明细 ----
print('===== 三分类终裁变化（旧→新） =====')
changed = []
for r in triage:
    t = r.get('task_name')
    old_v = old_matrix.get(t)
    new_v = r.get('final_verdict')
    if old_v != new_v:
        changed.append((t, labels.get(t, '?'), old_v, new_v))
print(f'共 {len(changed)} 个视频终裁变化:')
for t, lb, o, n in changed:
    print(f'  {t:>6s} ({lb}): {o} → {n}')
