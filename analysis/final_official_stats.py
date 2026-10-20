# -*- coding: utf-8 -*-
"""200集官方实跑留档：混淆矩阵（三分类+全自动）、误报漏检清单、运行记录。"""
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
print('结果文件:', files[-1].split('\\')[-1], '| 视频数:', len(results))

# 标签
labels = {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        labels[row['video'].rsplit('.', 1)[0]] = row['label']


def matrix(rs):
    m = {'real': {}, 'fake': {}}
    for x in rs:
        t = str(x.get('task_name'))
        lb = labels.get(t.rsplit('.', 1)[0], '?')
        if lb not in m:
            continue
        v = x.get('final_verdict', '?')
        m[lb][v] = m[lb].get(v, 0) + 1
    return m


mt = matrix(results)
print()
print('===== 三分类模式官方混淆矩阵 =====')
print('真实组(100):', mt['real'])
print('伪造组(100):', mt['fake'])
tp = mt['fake'].get('伪造', 0)
fn = mt['fake'].get('无伪造', 0)
fp = mt['real'].get('伪造', 0)
tn = mt['real'].get('无伪造', 0)
sus = mt['fake'].get('存疑', 0) + mt['real'].get('存疑', 0)
print(f'硬检出={tp} 硬漏检={fn} 硬误报={fp} 硬正确={tn} 存疑={sus} ({sus/2:.1f}%)')

# 全自动口径
auto = copy.deepcopy(results)
for x in auto:
    refinalize(x, auto=True, prior_fake_thr=0.55, prior_real_thr=0.45)
ma = matrix(auto)
print()
print('===== 全自动模式官方混淆矩阵（0.55阈值） =====')
print('真实组(100):', ma['real'])
print('伪造组(100):', ma['fake'])
atp = ma['fake'].get('伪造', 0)
afp = ma['real'].get('伪造', 0)
print(f'检出={atp}% 误报={afp}% 综合正确率={(atp + 100 - afp) / 2:.1f}%')

# 误报漏检清单
print()
print('===== 误报/漏检清单 =====')
print('硬漏检(伪造被判无伪造):', sorted(t for t, lb in labels.items() if lb == 'fake'
      and any(str(x.get('task_name')).rsplit('.', 1)[0] == t and x.get('final_verdict') == '无伪造' for x in results)))
print('硬误报(真实被判伪造):', sorted(t for t, lb in labels.items() if lb == 'real'
      and any(str(x.get('task_name')).rsplit('.', 1)[0] == t and x.get('final_verdict') == '伪造' for x in results)))
print('存疑的真实:', sorted(t for t, lb in labels.items() if lb == 'real'
      and any(str(x.get('task_name')).rsplit('.', 1)[0] == t and x.get('final_verdict') == '存疑' for x in results)))
print('存疑的伪造数:', sus - len([t for t, lb in labels.items() if lb == 'real'
      and any(str(x.get('task_name')).rsplit('.', 1)[0] == t and x.get('final_verdict') == '存疑' for x in results)]))

# 留档
with open(BASE + r'\output\official_final_summary.json', 'w', encoding='utf-8') as f:
    json.dump({'triage': {k: v for k, v in mt.items()},
               'auto055': {k: v for k, v in ma.items()},
               'source': files[-1].split('\\')[-1]}, f, ensure_ascii=False, indent=2)
print()
print('saved output/official_final_summary.json')
