# -*- coding: utf-8 -*-
"""200视频检测结果分析：逐视频信号明细（CV各信号+模型各票）+ 分组统计表 + CSV明细。"""
import csv
import glob
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
files = sorted(glob.glob(BASE + r'\output_full200\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
results = r['results']

labels = {}
table_prior = {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        table_prior[k] = float(row['prior'])


def parse_verdict(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


def parse_cv_verify(content):
    m = re.search(r'面颈纹理跳变核验[：:]\s*\**\s*(支持|反对|无法判定)', content or '')
    return m.group(1) if m else '无'


rows = []
for x in results:
    t = str(x.get('task_name')).rsplit('.', 1)[0]
    lb = labels.get(t, '?')
    c = x.get('content') or ''
    iv = parse_verdict(c)
    ev = x.get('evidence_score', 0)
    cv = parse_cv_verify(c)
    fv = x.get('final_verdict', '?')
    correct = ''
    if lb == 'fake':
        correct = '漏检' if fv == '无伪造' else ('检出' if fv in ('伪造',) else '存疑')
    else:
        correct = '误报' if fv == '伪造' else ('正确' if fv == '无伪造' else '存疑')
    rows.append({
        'video': t, 'label': lb, 'prior': round(x.get('prior_p') or 0, 3),
        'table_prior': round(table_prior.get(t, 0), 3),
        'evidence': ev, 'cv_verify': cv,
        'init_vote': iv, 'final': fv, 'result': correct,
        'phys': round(x.get('phys_guard', 0), 1) if x.get('phys_guard') else '—',
    })

# CSV 明细
with open(BASE + r'\output\200视频检测明细.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['video', 'label', 'prior', 'table_prior', 'phys',
                                      'evidence', 'cv_verify', 'init_vote', 'final', 'result'])
    w.writeheader()
    w.writerows(rows)
print('CSV已保存: output/200视频检测明细.csv (%d行)' % len(rows))

# 分组统计
from collections import Counter


def stats(key, vals_dict):
    fc, rc = Counter(), Counter()
    for r in rows:
        v = str(r.get(key))
        (fc if r['label'] == 'fake' else rc)[v] += 1
    return fc, rc


print()
print('===== 各信号在真假组的表现 =====')
print('【CV·先验（实时）】')
fr = [r['prior'] for r in rows if r['label'] == 'fake']
rr = [r['prior'] for r in rows if r['label'] == 'real']
print('  伪造组: ≥0.55有%d个，≥0.60有%d个，<0.45有%d个' % (
    sum(1 for v in fr if v >= 0.55), sum(1 for v in fr if v >= 0.60), sum(1 for v in fr if v < 0.45)))
print('  真实组: ≥0.55有%d个，≥0.60有%d个' % (
    sum(1 for v in rr if v >= 0.55), sum(1 for v in rr if v >= 0.60)))
print('【CV·证据子分（控方逐项异常计数）】')
fc, rc = stats('evidence', None)
print('  伪造组: ≥3有%d个，0有%d个 | 真实组: ≥3有%d个，0有%d个' % (
    sum(1 for r in rows if r['label'] == 'fake' and r['evidence'] >= 3),
    sum(1 for r in rows if r['label'] == 'fake' and r['evidence'] == 0),
    sum(1 for r in rows if r['label'] == 'real' and r['evidence'] >= 3),
    sum(1 for r in rows if r['label'] == 'real' and r['evidence'] == 0)))
print('【模型·初筛保守票】')
fc, rc = stats('init_vote', None)
print('  伪造组: 判伪造%d个 | 真实组: 判伪造%d个' % (fc.get('伪造', 0), rc.get('伪造', 0)))
print('【模型·CV可视化核验】')
fc, rc = stats('cv_verify', None)
print('  伪造组: 支持%d 反对%d | 真实组: 支持%d 反对%d' % (
    fc.get('支持', 0), fc.get('反对', 0), rc.get('支持', 0), rc.get('反对', 0)))
print('【终裁表现】')
fc, rc = stats('final', None)
print('  伪造组:', dict(fc))
print('  真实组:', dict(rc))

# 分组表现：真实组存疑/误报的组成
print()
print('===== 真实组20个非"无伪造"样本（存疑+误报）的成因 =====')
for r in rows:
    if r['label'] == 'real' and r['final'] != '无伪造':
        print('  %s: 终裁=%s 先验=%.3f 证据子分=%d 核验=%s 初筛票=%s' % (
            r['video'], r['final'], r['prior'], r['evidence'], r['cv_verify'], r['init_vote']))
