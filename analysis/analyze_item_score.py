# -*- coding: utf-8 -*-
"""控方证据子分设计：分离性单项集 {2,4,7,10,11,12,13} 的异常计数阈值扫描。
目标：在低清分支区分 26 个 CV 漏检伪造 与 10 个低先验真实。"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
SET = {'2', '4', '7', '10', '11', '12', '13'}

contents = {}
for path in (BASE + r'\output_pcal\results_2026-08-26T14-01-57Z.json',
             BASE + r'\output_pcal2\results_2026-08-26T16-40-33Z.json'):
    r = json.load(open(path, encoding='utf-8'))
    for x in r['results']:
        contents[str(x.get('task_name'))] = x.get('content') or ''


def parse_abnormal(content):
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
    return out


fakes = ['F18', 'F19', 'F30', 'F32', 'F33', 'F34', 'F42', 'F45', 'F46',
         'F5', 'F6', 'F69', 'F7', 'F70', 'F76', 'F77', 'F8', 'F82',
         'F1', 'F16', 'F39', 'F58', 'F62', 'F81', 'F87', 'F88']
low_reals = ['2', '3', '5', '10', '14', '18', '77', '94', '96', '99']

scores = {}
for v, c in contents.items():
    scores[v] = len(parse_abnormal(c) & SET)

print('证据子分（7 个分离性单项的异常计数）:')
print()
print('CV漏检伪造 (n=%d):' % sum(1 for v in fakes if v in scores), sorted(scores[v] for v in fakes if v in scores))
print('低先验真实 (n=%d):' % sum(1 for v in low_reals if v in scores), sorted(scores[v] for v in low_reals if v in scores))
print()
print('===== 阈值扫描（子分≥T → 判可疑/伪造信号） =====')
for T in range(1, 8):
    f_hit = sum(1 for v in fakes if scores.get(v, 0) >= T)
    r_hit = sum(1 for v in low_reals if scores.get(v, 0) >= T)
    print(f'  T={T}: 漏检伪造命中 {f_hit}/26  低先验真实命中 {r_hit}/10')
print()
print('===== 逐视频明细 =====')
for v in sorted(fakes + low_reals):
    if v in scores:
        print(f'  {v:>5s} 子分={scores[v]}  {"伪造" if v in fakes else "真实"}')
