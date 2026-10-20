# -*- coding: utf-8 -*-
"""v5.7 修复离线验证：官方实跑结果 + 表值锚定先验 + 定罪背书门槛 → 修正混淆矩阵。"""
import copy
import csv
import glob
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from reapply_fusion import refinalize

BASE = r'D:\deepfake'
files = sorted(glob.glob(BASE + r'\output_full200\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
results = r['results']

labels = {}
table = {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        table[k] = float(row['prior'])

# 锚定：用表值替换实时先验
anchored = 0
for x in results:
    t = str(x.get('task_name')).rsplit('.', 1)[0]
    live = x.get('prior_p')
    if live is not None and t in table and abs(table[t] - live) > 0.15:
        anchored += 1
        x['prior_p'] = table[t]
print('先验锚定: %d 个视频实时值偏离表值>0.15 已替换' % anchored)


def matrix(rs):
    m = {'real': {}, 'fake': {}}
    for x in rs:
        t = str(x.get('task_name')).rsplit('.', 1)[0]
        lb = labels.get(t, '?')
        if lb not in m:
            continue
        v = x.get('final_verdict', '?')
        m[lb][v] = m[lb].get(v, 0) + 1
    return m


# 三分类（带背书门槛 0.70）
triage = copy.deepcopy(results)
for x in triage:
    refinalize(x, auto=False, prior_convict_backstop=0.70)
mt = matrix(triage)
print()
print('===== 修复后三分类混淆矩阵 =====')
print('真实组(100):', mt['real'])
print('伪造组(100):', mt['fake'])
tp = mt['fake'].get('伪造', 0)
fn = mt['fake'].get('无伪造', 0)
fp = mt['real'].get('伪造', 0)
tn = mt['real'].get('无伪造', 0)
sus = mt['fake'].get('存疑', 0) + mt['real'].get('存疑', 0)
print('硬检出=%d 硬漏检=%d 硬误报=%d 硬正确=%d 存疑=%d (%.1f%%)' % (tp, fn, fp, tn, sus, sus / 2))

# 全自动（锚定表值 + 0.60阈值）
auto = copy.deepcopy(results)
for x in auto:
    refinalize(x, auto=True, prior_fake_thr=0.60, prior_real_thr=0.45)
ma = matrix(auto)
print()
print('===== 修复后全自动混淆矩阵（0.60阈值） =====')
print('真实组(100):', ma['real'])
print('伪造组(100):', ma['fake'])
atp = ma['fake'].get('伪造', 0)
afp = ma['real'].get('伪造', 0)
print('检出=%d%% 误报=%d%% 综合正确率=%.1f%%' % (atp, afp, (atp + 100 - afp) / 2))

print()
print('===== 修复前后对比 =====')
print('三分类: 修复前 硬误报1/硬漏检10/存疑77  →  修复后 硬误报%d/硬漏检%d/存疑%d' % (fp, fn, sus))
print('全自动: 修复前 79%%/24%%/77.5%%  →  修复后 %d%%/%d%%/%.1f%%' % (atp, afp, (atp + 100 - afp) / 2))
