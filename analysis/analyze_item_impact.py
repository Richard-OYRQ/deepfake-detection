# -*- coding: utf-8 -*-
"""控方证据子分接入后的全自动模拟（v5.4 + 证据子分≥3 定罪）：
低清分支：先验≥0.55 → 伪造；证据子分≥3 → 伪造；否则无伪造
高清分支：模型保守票 → 无伪造
所有需要子分的低清视频均在48校准样本内（26漏检伪造+10低先验真实全覆盖）。"""
import csv
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import cv2

BASE = r'D:\deepfake'
SET = {'2', '4', '7', '10', '11', '12', '13'}
THR = 3

# 标签+先验
labels, cv_prior = {}, {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        cv_prior[k] = float(row['prior'])

# 分辨率
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


def parse_score(content):
    out = set()
    in_table = False
    for line in (content or '').splitlines():
        s = line.strip()
        if s.startswith('| # |') or s.startswith('|---'):
            in_table = True
            continue
        if in_table and s.startswith('|'):
            cols = [c.strip() for c in s.split('|')]
            if len(cols) >= 4 and cols[1].isdigit():
                rating = cols[3].strip().strip('*').strip()
                if rating == '异常':
                    out.add(cols[1])
            elif cols and cols[1] and not cols[1].isdigit():
                break
    return len(out & SET)


scores = {}
for path in (BASE + r'\output_pcal\results_2026-08-26T14-01-57Z.json',
             BASE + r'\output_pcal2\results_2026-08-26T16-40-33Z.json'):
    r = json.load(open(path, encoding='utf-8'))
    for x in r['results']:
        scores[str(x.get('task_name'))] = parse_score(x.get('content') or '')

# 低清低先验真实的子分（确认误伤面）
print('低清低先验真实（证据子分误伤风险名单）:')
for k, lb in sorted(labels.items()):
    if lb != 'real':
        continue
    w, h = res_map.get(k, (0, 0))
    hi = w >= 1280 and h >= 720
    p = cv_prior.get(k, 0)
    if not hi and p < 0.55:
        sc = scores.get(k, -1)
        print(f'  {k:>4s} {w}x{h} 先验={p:.2f} 子分={sc}')

print()
print('===== 全自动模拟（v5.4 + 证据子分定罪 T=3） =====')
mf = {'无伪造': 0, '伪造': 0}
mr = {'无伪造': 0, '伪造': 0}
changed = []
for k, lb in labels.items():
    w, h = res_map.get(k, (0, 0))
    hi = w >= 1280 and h >= 720
    p = cv_prior.get(k, 0)
    sc = scores.get(k, 0)
    if hi:
        v = '无伪造'  # 模型保守票主导
    else:
        v = '伪造' if (p >= 0.55 or sc >= THR) else '无伪造'
    (mf if lb == 'fake' else mr)[v] += 1
    if lb == 'fake' and v == '伪造' and p < 0.55:
        changed.append((k, p, sc))
print(f'伪造组: {mf}')
print(f'真实组: {mr}')
acc = (mf['伪造'] + mr['无伪造']) / 200 * 100
print(f'综合正确率 = {acc:.1f}%')
print()
print(f'证据子分新定罪的低清漏检伪造 {len(changed)} 个:')
for k, p, sc in changed:
    print(f'  {k}: 先验={p:.2f} 子分={sc}')
