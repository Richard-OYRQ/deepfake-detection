# -*- coding: utf-8 -*-
"""最终确认：4 个低清低先验真实的证据子分 + 全自动终态模拟。"""
import csv
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2

from src.preprocessor import prosecutor_evidence_score

BASE = r'D:\deepfake'

files = sorted(glob.glob(BASE + r'\output_pcal3\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
scores = {}
for x in r['results']:
    t = str(x.get('task_name'))
    if x.get('error'):
        print(f'{t}: 失败')
        continue
    sc = prosecutor_evidence_score(x.get('content') or '')
    scores[t] = sc
    print(f'{t}: 证据子分 = {sc}')

# 合并全部校准数据 → 全自动终态模拟
for path in (BASE + r'\output_pcal\results_2026-08-26T14-01-57Z.json',
             BASE + r'\output_pcal2\results_2026-08-26T16-40-33Z.json'):
    rr = json.load(open(path, encoding='utf-8'))
    for x in rr['results']:
        t = str(x.get('task_name'))
        if t not in scores:
            scores[t] = prosecutor_evidence_score(x.get('content') or '')

labels, cv_prior = {}, {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        cv_prior[k] = float(row['prior'])

res_map = {}
for d, sel in ((os.path.join(BASE, 'videos'), lambda s: s.isdigit()),
               (os.path.join(BASE, '待鉴别'), lambda s: True)):
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith('.mp4'):
            continue
        stem = f.split('.')[0]
        if not sel(stem):
            continue
        cap = cv2.VideoCapture(os.path.join(d, f))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        res_map[stem] = (w, h)

THR = 3
mf = {'无伪造': 0, '伪造': 0}
mr = {'无伪造': 0, '伪造': 0}
uncalibrated = []
for k, lb in labels.items():
    w, h = res_map.get(k, (0, 0))
    hi = w >= 1280 and h >= 720
    p = cv_prior.get(k, 0)
    sc = scores.get(k, -1)
    if hi:
        v = '无伪造'
    else:
        if sc < 0 and p < 0.55:
            uncalibrated.append((k, lb))
        v = '伪造' if (p >= 0.55 or sc >= THR) else '无伪造'
    (mf if lb == 'fake' else mr)[v] += 1
print()
print('===== v5.5 全自动终态（自适应路由 + 控方证据子分≥3） =====')
print(f'伪造组: {mf}')
print(f'真实组: {mr}')
acc = (mf['伪造'] + mr['无伪造']) / 200 * 100
print(f'综合正确率 = {acc:.1f}%')
print(f'未校准的低清低先验视频（按无伪造处理）: {uncalibrated}')
