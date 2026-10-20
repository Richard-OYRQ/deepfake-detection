# -*- coding: utf-8 -*-
"""控方逐项证据挖掘：48段控方输出中，14项逐项"异常"评级在
CV漏检伪造 vs 低先验真实 vs 高先验真实 三组间的差异。"""
import csv
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
GROUPS = {
    'cv_miss_fake': ['F18', 'F19', 'F30', 'F32', 'F33', 'F34', 'F42', 'F45', 'F46',
                     'F5', 'F6', 'F69', 'F7', 'F70', 'F76', 'F77', 'F8', 'F82',
                     'F1', 'F16', 'F39', 'F58', 'F62', 'F81', 'F87', 'F88'],
    'low_real': ['2', '3', '5', '10', '14', '18', '77', '94', '96', '99'],
    'high_real': ['1', '15', '20', '29', '35', '53', '58', '59', '63', '67'],
}

ITEMS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14']


def parse_items(content):
    """从控方输出的逐项判定表提取每项评级。返回 {item: 评级}。"""
    out = {}
    in_table = False
    for line in (content or '').splitlines():
        s = line.strip()
        if s.startswith('| # |') or s.startswith('|---'):
            in_table = True
            continue
        if in_table and s.startswith('|'):
            cols = [c.strip() for c in s.split('|')]
            if len(cols) >= 4 and cols[1] in ITEMS:
                rating = cols[3].strip().strip('*').strip()
                if rating in ('正常', '可疑', '异常'):
                    out[cols[1]] = rating
            elif cols and cols[1] not in ITEMS and cols[1]:
                break
    return out


contents = {}
for path, prefix in ((BASE + r'\output_pcal\results_2026-08-26T14-01-57Z.json', ''),
                     (BASE + r'\output_pcal2\results_2026-08-26T16-40-33Z.json', '')):
    r = json.load(open(path, encoding='utf-8'))
    for x in r['results']:
        t = str(x.get('task_name'))
        contents[t] = x.get('content') or ''

print('解析到逐项判定的视频数:', sum(1 for c in contents.values() if parse_items(c)))
print()
print('===== 各组"异常"评级率（异常项数/14 项均值） =====')
for grp, vids in GROUPS.items():
    rates = []
    for v in vids:
        if v not in contents:
            continue
        items = parse_items(contents[v])
        if not items:
            continue
        abnormal = sum(1 for k, r in items.items() if r == '异常')
        susp = sum(1 for k, r in items.items() if r == '可疑')
        rates.append((abnormal, susp, len(items)))
    if rates:
        ab_mean = sum(r[0] for r in rates) / len(rates)
        sp_mean = sum(r[1] for r in rates) / len(rates)
        print(f'  {grp:<14s}: 平均异常 {ab_mean:.1f}/14  平均可疑 {sp_mean:.1f}/14  (n={len(rates)})')
print()
print('===== 逐项"异常"率对比（重点看区分度） =====')
print(f'{"项":>4s} {"CV漏检伪造":>10s} {"低先验真实":>10s} {"高先验真实":>10s} {"区分方向":>10s}')
for item in ITEMS:
    row = []
    for grp, vids in GROUPS.items():
        n_ab = 0
        n_total = 0
        for v in vids:
            if v not in contents:
                continue
            items = parse_items(contents[v])
            if item in items:
                n_total += 1
                if items[item] == '异常':
                    n_ab += 1
        row.append(f'{n_ab}/{n_total}')
    fake_rate = int(row[0].split('/')[0]) / max(1, int(row[0].split('/')[1]))
    low_rate = int(row[1].split('/')[0]) / max(1, int(row[1].split('/')[1]))
    direction = ''
    if fake_rate - low_rate >= 0.15:
        direction = '伪造更高'
    elif low_rate - fake_rate >= 0.15:
        direction = '真实更高'
    print(f'{item:>4s} {row[0]:>10s} {row[1]:>10s} {row[2]:>10s} {direction:>10s}')
