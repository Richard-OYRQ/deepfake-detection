# -*- coding: utf-8 -*-
"""
按最新检测策略统计 200 个视频的最终检出情况：
- 40个最难样本（20真+20伪）：用 B方案轮融合结果（旧提示词控方票 + prior_p）
- 其余 160 个：用全量轮融合结果（特征表先验回退）
"""
import json
import os

BASE = r'D:\deepfake'

with open(os.path.join(BASE, 'output_pilot', 'results_2026-08-23T14-25-02Z_refused.json'), encoding='utf-8') as f:
    b_run = {r['task_name']: r for r in json.load(f)['results']}
with open(os.path.join(BASE, 'output', 'results_2026-08-23T09-12-51Z_refused.json'), encoding='utf-8') as f:
    full_run = {r['task_name']: r for r in json.load(f)['results']}

assert len(b_run) == 40 and len(full_run) == 200

out = []
def p(line=''):
    out.append(str(line))

# 合并：40个用B轮，其余用全量轮
merged = {}
for name, r in full_run.items():
    merged[name] = b_run.get(name, r)

# 统计
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
susp_r = real.get('存疑', 0)
susp_f = fake.get('存疑', 0)
fail = real.get('失败', 0) + fake.get('失败', 0)

hard_correct = tp + tn
hard_wrong = fp + fn
deferred = susp_r + susp_f + fail
decided = n_total - deferred

p('=' * 62)
p('  200 视频最新策略检出统计（融合终裁）')
p('=' * 62)
p()
p('===== 混淆矩阵（标注 vs 终裁） =====')
p(f'{"标注\\终裁":<10s} {"无伪造":>7s} {"伪造":>7s} {"存疑":>7s} {"失败":>7s} {"合计":>7s}')
p(f'{"真实":<10s} {tn:>7d} {fp:>7d} {susp_r:>7d} {real.get("失败",0):>7d} {n_real:>7d}')
p(f'{"伪造":<10s} {fn:>7d} {tp:>7d} {susp_f:>7d} {fake.get("失败",0):>7d} {n_fake:>7d}')
p()
p('===== 核心指标 =====')
p(f'伪造检出率（敏感性）: {tp}/{n_fake} = {tp/n_fake*100:.1f}%')
p(f'真实误报率（1-特异性）: {fp}/{n_real} = {fp/n_real*100:.1f}%')
p(f'真实正确率（特异性）: {tn}/{n_real} = {tn/n_real*100:.1f}%')
p(f'伪造漏检率: {fn}/{n_fake} = {fn/n_fake*100:.1f}%')
p(f'存疑率: 真实 {susp_r}/{n_real} ({susp_r/n_real*100:.0f}%), 伪造 {susp_f}/{n_fake} ({susp_f/n_fake*100:.0f}%)')
p()
p('===== 综合正确率（三种口径） =====')
p(f'① 硬判正确率（存疑/失败计入错误）: {hard_correct}/{n_total} = {hard_correct/n_total*100:.1f}%')
p(f'② 硬判正确率（存疑/失败剔除，只算明确判定）: {hard_correct}/{decided} = {hard_correct/decided*100:.1f}%  (明确判定 {decided} 个)')
p(f'③ 硬判错误率: {hard_wrong}/{n_total} = {hard_wrong/n_total*100:.1f}%  '
  f'(误报{fp} + 漏检{fn}，其余 {deferred} 个转人工复核)')
p()
p('===== 新旧系统对比 =====')
p(f'{"指标":<22s} {"旧系统":>14s} {"最新策略":>14s}')
p(f'{"伪造检出率":<22s} {"91% (91/100)":>14s} {f"{tp/n_fake*100:.0f}% ({tp}/100)":>14s}')
p(f'{"真实误报率":<22s} {"82% (82/100)":>14s} {f"{fp/n_real*100:.0f}% ({fp}/100)":>14s}')
p(f'{"真实正确率":<22s} {"18%":>14s} {f"{tn/n_real*100:.0f}%":>14s}')
p(f'{"硬判错误总数":<22s} {"91 (82误报+9漏检)":>14s} {f"{hard_wrong} ({fp}误报+{fn}漏检)":>14s}')
p(f'{"人工复核量":<22s} {"0":>14s} {f"{deferred} ({deferred/n_total*100:.0f}%)":>14s}')
p(f'{"硬判正确率(口径②)":<22s} {"54.5%":>14s} {f"{hard_correct/decided*100:.1f}%":>14s}')
p()
p('===== 说明 =====')
p('最新策略 = v5.1提示词 + 先验路由控方轮 + 融合终裁（任一伪造票∧先验≥0.70→伪造；冲突/分裂→存疑）')
p('40个最难样本采用含旧提示词控方轮的B方案实测结果；其余160个采用全量轮结果离线融合（特征表先验）')
p('注：40样本人为挑选为最难案例（12高先验真实+9隐形伪造），故全量数字略偏保守')

with open(os.path.join(BASE, 'output', '_final_stats.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
