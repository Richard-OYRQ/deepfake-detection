# -*- coding: utf-8 -*-
"""全自动模式 200 视频合并统计：40个最难样本用B轮auto结果，其余用全量轮auto结果"""
import json
import os

BASE = r'D:\deepfake'

with open(os.path.join(BASE, 'output_pilot', 'results_2026-08-23T14-25-02Z_auto.json'), encoding='utf-8') as f:
    b_run = {r['task_name']: r for r in json.load(f)['results']}
with open(os.path.join(BASE, 'output', 'results_2026-08-23T09-12-51Z_auto.json'), encoding='utf-8') as f:
    full_run = {r['task_name']: r for r in json.load(f)['results']}

merged = {}
for name, r in full_run.items():
    merged[name] = b_run.get(name, r)

matrix = {}
for name, r in merged.items():
    gt = 'fake' if name.startswith('F') else 'real'
    fv = r.get('final_verdict', '失败')
    matrix.setdefault(gt, {})
    matrix[gt][fv] = matrix[gt].get(fv, 0) + 1

real = matrix['real']
fake = matrix['fake']
n_real = sum(real.values())
n_fake = sum(fake.values())
n_total = n_real + n_fake

tp = fake.get('伪造', 0)
tn = real.get('无伪造', 0)
fp = real.get('伪造', 0)
fn = fake.get('无伪造', 0)

out = []
def p(line=''):
    out.append(str(line))

p('=' * 60)
p('  200 视频 · 全自动判决模式（无人工复核）统计')
p('=' * 60)
p()
p('===== 混淆矩阵（标注 vs 终裁） =====')
p(f'{"标注\\终裁":<10s} {"无伪造":>7s} {"伪造":>7s} {"失败":>7s} {"合计":>7s}')
p(f'{"真实":<10s} {tn:>7d} {fp:>7d} {real.get("失败",0):>7d} {n_real:>7d}')
p(f'{"伪造":<10s} {fn:>7d} {tp:>7d} {fake.get("失败",0):>7d} {n_fake:>7d}')
p()
p('===== 核心指标 =====')
p(f'伪造检出率（敏感性）: {tp}/{n_fake} = {tp/n_fake*100:.1f}%')
p(f'真实误报率: {fp}/{n_real} = {fp/n_real*100:.1f}%')
p(f'真实正确率（特异性）: {tn}/{n_real} = {tn/n_real*100:.1f}%')
p(f'伪造漏检率: {fn}/{n_fake} = {fn/n_fake*100:.1f}%')
p(f'综合硬判正确率: {tp+tn}/{n_total} = {(tp+tn)/n_total*100:.1f}%')
p()
p('===== 与各方案对比 =====')
p(f'{"方案":<26s} {"检出":>7s} {"误报":>7s} {"综合正确":>8s}')
p(f'{"旧系统（原始）":<26s} {"91.0%":>7s} {"82.0%":>7s} {"54.5%":>8s}')
p(f'{"三分类+人工复核（前版）":<26s} {"7.0%":>7s} {"1.0%":>7s} {"46.5%*":>8s}')
p(f'{"全自动（本轮，先验0.60）":<26s} {f"{tp/n_fake*100:.1f}%":>7s} {f"{fp/n_real*100:.1f}%":>7s} {f"{(tp+tn)/n_total*100:.1f}%":>8s}')
p()
p('* 前版口径：硬判正确率（存疑计入错误）；若计入人工复核救回，约 95%')
p()
p('注：40个最难样本人为加权（B方案实测），其余160个为全量轮离线重算')

with open(os.path.join(BASE, 'output', '_auto_stats.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
