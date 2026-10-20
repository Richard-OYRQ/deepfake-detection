# -*- coding: utf-8 -*-
"""证据分析师校准结果分析：P(伪造) 打分分布、AUC、与控方票/先验对比。"""
import csv
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
import glob
files = sorted(glob.glob(BASE + r'\output_analyst\results*.json'))
assert files, 'no analyst results'
r = json.load(open(files[-1], encoding='utf-8'))
print('results file:', files[-1].split('\\')[-1])

labels = {}
cv = {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        cv[k] = float(row['prior'])

# 控方票（同批40视频，对比用）
pcal = json.load(open(BASE + r'\output_pcal\results_2026-08-26T14-01-57Z.json', encoding='utf-8'))


def parse_v(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


def parse_p(content):
    m = re.search(r'P\s*[（(]?\s*伪造\s*[）)]?\s*[=：:]\s*\**\s*(\d+)\s*/\s*100', content or '')
    if m:
        return int(m.group(1))
    m2 = re.search(r'P\(伪造\)\s*=\s*(\d+)', content or '')
    return int(m2.group(1)) if m2 else None


pros = {str(x.get('task_name')): parse_v(x.get('content')) for x in pcal['results']}

rows = []
for x in r['results']:
    t = str(x.get('task_name', ''))
    rows.append({
        'name': t,
        'label': labels.get(t, '?'),
        'p': parse_p(x.get('content')) if not x.get('error') else None,
        'error': x.get('error'),
        'pros': pros.get(t, '?'),
        'cv': cv.get(t, 0),
    })

ok = [x for x in rows if x['p'] is not None]
print(f'解析到 P(伪造) 的: {len(ok)}/40（{sum(1 for x in rows if x["error"])} 个失败）')

print()
print('===== 分析师打分明细 =====')
for x in rows:
    pv = str(x['p']) if x['p'] is not None else '无'
    print(f"{x['name']:>5s} {x['label']:>4s} P={pv:>4s} "
          f"控方={x['pros']:<5s} CV={x['cv']:.2f}")


def rank_auc(rv, fv):
    if not rv or not fv:
        return float('nan')
    allv = list(rv) + list(fv)
    nr = len(rv)
    ranks = {i: q for q, i in enumerate(sorted(range(len(allv)), key=lambda k: allv[k]))}
    sr = sum(ranks[i] for i in range(nr, nr + len(fv)))
    return (sr - len(fv) * (len(fv) + 1) / 2) / (nr * len(fv))


fp = [x['p'] for x in ok if x['label'] == 'fake']
rp = [x['p'] for x in ok if x['label'] == 'real']
auc = rank_auc(rp, fp)
print()
print(f'===== 分析师 P(伪造) 分布 =====')
import numpy as np
print(f'伪造组: 均值={np.mean(fp):.1f} 中位={np.median(fp):.0f} 范围=[{min(fp)},{max(fp)}]  (n={len(fp)})')
print(f'真实组: 均值={np.mean(rp):.1f} 中位={np.median(rp):.0f} 范围=[{min(rp)},{max(rp)}]  (n={len(rp)})')
print(f'秩基AUC (P(fake>real)): {auc:.3f}  |AUC-0.5|={abs(auc - 0.5):.3f}')

print()
print('===== 阈值扫描（分析师P≥T → 判伪造） =====')
for T in (50, 55, 60, 65, 70):
    tp = sum(1 for p in fp if p >= T)
    fpr = sum(1 for p in rp if p >= T)
    print(f'  T={T}: 检出={tp}/{len(fp)} 误报={fpr}/{len(rp)}')

print()
print('===== 18 个 CV 漏检伪造的分析师打分 =====')
miss = ['F18', 'F19', 'F30', 'F32', 'F33', 'F34', 'F42', 'F45', 'F46',
        'F5', 'F6', 'F69', 'F7', 'F70', 'F76', 'F77', 'F8', 'F82']
for x in rows:
    if x['name'] in miss:
        print(f"  {x['name']}: P={x['p']}  控方={x['pros']}")
