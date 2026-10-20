# -*- coding: utf-8 -*-
"""v5.2 全自动模式阈值扫描（已并入 15.mp4 补跑结果的官方三分类文件）。"""
import copy
import csv
import json
import sys

sys.path.insert(0, r'D:\deepfake')

from reapply_fusion import refinalize

labels = {}
with open(r'D:\deepfake\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        labels[row['video'].rsplit('.', 1)[0]] = row['label']

p = json.load(open(r'D:\deepfake\output\results_v52_三分类_融合先验_20260826.json', encoding='utf-8'))

for thr in (0.55, 0.60, 0.65):
    m = {'real': {}, 'fake': {}}
    for r in copy.deepcopy(p['results']):
        refinalize(r, auto=True, prior_fake_thr=thr, prior_real_thr=0.45)
        lb = labels.get(r.get('task_name'))
        v = r.get('final_verdict')
        m[lb][v] = m[lb].get(v, 0) + 1
    tp = m['fake'].get('伪造', 0)
    fp = m['real'].get('伪造', 0)
    fn = m['fake'].get('无伪造', 0)
    acc = (tp + (100 - fp)) / 200 * 100
    print(f'{thr}: 检出 {tp}% | 漏检 {fn} | 误报 {fp}% | 综合 {acc:.1f}%')
