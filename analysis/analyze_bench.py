# -*- coding: utf-8 -*-
"""配对基准集检测分析：保守票/控方票/逐项证据在 14 对上的判别力。"""
import glob
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from src.preprocessor import prosecutor_evidence_score

NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]


def parse_v(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


def parse_items(content):
    out = {}
    in_table = False
    for line in (content or '').splitlines():
        s = line.strip()
        if s.startswith('| # |') or s.startswith('|---'):
            in_table = True
            continue
        if in_table and s.startswith('|'):
            cols = [c.strip() for c in s.split('|')]
            if len(cols) >= 4 and cols[1].isdigit():
                out[cols[1]] = cols[3].strip().strip('*').strip()
            elif cols and cols[1] and not cols[1].isdigit():
                break
    return out


def load(d):
    files = sorted(glob.glob(r'D:\deepfake\%s\results*.json' % d))
    if not files:
        return {}
    r = json.load(open(files[-1], encoding='utf-8'))
    return {str(x.get('task_name')): (x.get('content') or '') for x in r['results']}


prod = load('output_benchprod')
pros = load('output_benchpros')

print('===== 保守票（生产路由） =====')
prod_fake = sum(1 for n in NUMS if parse_v(prod.get('fake_e%d_on_%d' % (n, n))) == '伪造')
prod_real = sum(1 for n in NUMS if parse_v(prod.get('%d' % n)) == '伪造')
print(f'假脸被判伪造: {prod_fake}/14   真视频被判伪造: {prod_real}/14')

print()
print('===== 控方票 =====')
pros_fake = sum(1 for n in NUMS if parse_v(pros.get('fake_e%d_on_%d' % (n, n))) == '伪造')
pros_real = sum(1 for n in NUMS if parse_v(pros.get('%d' % n)) == '伪造')
print(f'假脸被判伪造: {pros_fake}/14   真视频被判伪造: {pros_real}/14')

print()
print('===== 控方证据子分（7分离性单项异常计数） =====')
print(f'{"编号":>4s} {"假脸子分":>8s} {"真视频子分":>8s} {"差值":>6s}')
fake_scores, real_scores = [], []
for n in NUMS:
    fk = 'fake_e%d_on_%d' % (n, n)
    fs = prosecutor_evidence_score(pros.get(fk, ''))
    rs = prosecutor_evidence_score(pros.get('%d' % n, ''))
    fake_scores.append(fs)
    real_scores.append(rs)
    print(f'{n:>4d} {fs:>8d} {rs:>8d} {fs-rs:>+6d}')

import numpy as np
print()
print(f'假脸组: 均值={np.mean(fake_scores):.1f} 中位={np.median(fake_scores):.0f} 范围=[{min(fake_scores)},{max(fake_scores)}]')
print(f'真视频组: 均值={np.mean(real_scores):.1f} 中位={np.median(real_scores):.0f} 范围=[{min(real_scores)},{max(real_scores)}]')
# 成对检验：假-真差值分布
diffs = [f - r for f, r in zip(fake_scores, real_scores)]
print(f'成对差值: 均值={np.mean(diffs):+.1f} | 假>真的对数: {sum(1 for d in diffs if d > 0)}/14 | 假<真的对数: {sum(1 for d in diffs if d < 0)}/14')

print()
print('===== 逐项异常率（假脸 vs 真视频） =====')
for item in range(1, 15):
    i = str(item)
    fa = sum(1 for n in NUMS if parse_items(pros.get('fake_e%d_on_%d' % (n, n), '')).get(i) == '异常')
    ra = sum(1 for n in NUMS if parse_items(pros.get('%d' % n, '')).get(i) == '异常')
    if fa or ra:
        mark = ' <-- 假脸高' if fa > ra + 2 else (' <-- 真视频高' if ra > fa + 2 else '')
        print(f'  #{item:>2d}: 假脸 {fa:>2d}/14  真视频 {ra:>2d}/14{mark}')
