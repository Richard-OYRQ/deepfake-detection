# -*- coding: utf-8 -*-
"""全自动模式最终验证：稳定先验表(0.55阈值+边界带票) × 实际票型 → 200视频混淆矩阵"""
import csv
import json
import os

BASE = r'D:\deepfake'
FAKE_THR = 0.55
REAL_THR = 0.45

with open(os.path.join(BASE, 'output', 'stable_prior_table.csv'), encoding='utf-8-sig') as f:
    stable = {r['video'].rsplit('.', 1)[0]: r for r in csv.DictReader(f)}
with open(os.path.join(BASE, 'output_pilot', 'results_2026-08-23T14-25-02Z_refused.json'), encoding='utf-8') as f:
    b_run = {r['task_name']: r for r in json.load(f)['results']}
with open(os.path.join(BASE, 'output', 'results_2026-08-23T09-12-51Z_refused.json'), encoding='utf-8') as f:
    full_run = {r['task_name']: r for r in json.load(f)['results']}

rows = []
for name, row in stable.items():
    gt = row['label']
    prior = float(row['prior'])
    r = b_run.get(name) or full_run.get(name) or {}
    votes = r.get('vote_result') or {}
    fake_votes = sum(votes.get(k, 0) for k in ('换脸', '面部重演', '全生成'))
    if prior >= FAKE_THR:
        verdict = '伪造'
    elif prior < REAL_THR:
        verdict = '无伪造'
    else:
        verdict = '伪造' if fake_votes >= 1 else '无伪造'
    rows.append((name, gt, prior, verdict))

matrix = {'real': {}, 'fake': {}}
for name, gt, prior, verdict in rows:
    matrix[gt][verdict] = matrix[gt].get(verdict, 0) + 1

out = []
def p(line=''):
    out.append(str(line))

real, fake = matrix['real'], matrix['fake']
n_real = sum(real.values())
n_fake = sum(fake.values())
tp = fake.get('伪造', 0)
tn = real.get('无伪造', 0)
fp = real.get('伪造', 0)
fn = fake.get('无伪造', 0)

p('=' * 58)
p('  全自动模式最终验证（稳定先验 0.55 + 边界带票）')
p('=' * 58)
p()
p('===== 混淆矩阵 =====')
p(f'{"标注\\终裁":<10s} {"无伪造":>7s} {"伪造":>7s} {"合计":>7s}')
p(f'{"真实":<10s} {tn:>7d} {fp:>7d} {n_real:>7d}')
p(f'{"伪造":<10s} {fn:>7d} {tp:>7d} {n_fake:>7d}')
p()
p(f'伪造检出率: {tp}/{n_fake} = {tp/n_fake*100:.1f}%')
p(f'真实误报率: {fp}/{n_real} = {fp/n_real*100:.1f}%')
p(f'伪造漏检率: {fn}/{n_fake} = {fn/n_fake*100:.1f}%')
p(f'综合正确率: {tp+tn}/200 = {(tp+tn)/200*100:.1f}%')
p()
p('===== 误报真实视频（13个） =====')
p(', '.join(name for name, gt, prior, v in rows if gt == 'real' and v == '伪造'))
p()
p('===== 漏检伪造视频（3个） =====')
p(', '.join(f'{name}({prior:.2f})' for name, gt, prior, v in rows if gt == 'fake' and v == '无伪造'))
p()
p('===== 与目标对照 =====')
p(f'目标: 综合正确率 ≥ 91%')
p(f'实际: {(tp+tn)/200*100:.1f}%  {"达成 ✓" if (tp+tn)/200*100 >= 91 else "未达成 ✗"}')

with open(os.path.join(BASE, 'output', '_final_auto.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
