# -*- coding: utf-8 -*-
"""
全自动（无人工复核）方案模拟：
在 200 个标注视频上，评估"纯自动判决"能达到的性能上限。
信号：CV先验、模型伪造票数、模型无伪造票数、置信度
方法：逻辑回归 5 折交叉验证 + 规则方案对比
"""
import csv
import json
import os
import re

import numpy as np

BASE = r'D:\deepfake'


def parse_verdict(content):
    if not content:
        return 'unknown'
    for line in content.split('\n'):
        if '伪造类型判断' in line:
            if '无伪造' in line:
                return '无伪造'
            if '面部重演' in line:
                return '面部重演'
            if '换脸' in line:
                return '换脸'
            if '全生成' in line:
                return '全生成'
    return 'unknown'


def parse_conf(content):
    if not content:
        return 0
    m = re.search(r'置信度[：:]\s*\*{0,2}(\d+)\s*/\s*100', content)
    return int(m.group(1)) if m else 0


# ---- 合并 200 视频信号 ----
with open(os.path.join(BASE, 'output_pilot', 'results_2026-08-23T14-25-02Z_refused.json'), encoding='utf-8') as f:
    b_run = {r['task_name']: r for r in json.load(f)['results']}
with open(os.path.join(BASE, 'output', 'results_2026-08-23T09-12-51Z_refused.json'), encoding='utf-8') as f:
    full_run = {r['task_name']: r for r in json.load(f)['results']}

with open(os.path.join(BASE, 'src', 'prior_model.json'), encoding='utf-8') as f:
    model = json.load(f)
with open(os.path.join(BASE, 'output', 'feature_table.csv'), encoding='utf-8-sig') as f:
    rows = {r['video']: r for r in csv.DictReader(f)}


def feature_prior(row):
    z = model['bias']
    for name, mu, sd, w in zip(model['features'], model['mu'], model['sd'], model['weights']):
        x = float(row.get(name, 0) or 0)
        sd = sd if sd > 1e-9 else 1.0
        z += w * (x - mu) / sd
    return 1.0 / (1.0 + np.exp(-max(-30, min(30, z))))


videos = []
for name, r in full_run.items():
    row = rows.get(name + '.mp4')
    if row is None:
        continue
    gt = 1 if name.startswith('F') else 0
    prior = r.get('prior_p') or feature_prior(row)
    votes = r.get('vote_result') or {}
    fake_votes = sum(votes.get(k, 0) for k in ('换脸', '面部重演', '全生成'))
    real_votes = votes.get('无伪造', 0)
    conf = parse_conf(r.get('content', ''))
    verdict = parse_verdict(r.get('content', ''))
    videos.append((name, gt, prior, fake_votes, real_votes, conf, verdict))

n = len(videos)
X = np.array([[v[2], v[3], v[4], v[5]] for v in videos], dtype=float)
y = np.array([v[1] for v in videos])

out = []
def p(line=''):
    out.append(str(line))

p(f'===== 数据概况 =====')
p(f'总样本 {n}: 真实 {n - y.sum()}, 伪造 {y.sum()}')
p()

# ---- 逻辑回归 5 折 ----
def logistic_fit(Xs, yy, lr=0.2, epochs=800, l2=0.01):
    nn, dd = Xs.shape
    w = np.zeros(dd)
    b = 0.0
    for _ in range(epochs):
        z = Xs @ w + b
        prob = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        err = prob - yy
        w -= lr * (Xs.T @ err / nn + l2 * w)
        b -= lr * err.mean()
    return w, b


rng = np.random.RandomState(42)
idx = rng.permutation(n)
X, y = X[idx], y[idx]
metrics = []
for k in range(5):
    lo, hi = n * k // 5, n * (k + 1) // 5
    mask = np.ones(n, dtype=bool)
    mask[lo:hi] = False
    X_tr, y_tr = X[mask], y[mask]
    X_te, y_te = X[~mask], y[~mask]
    mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
    sd[sd < 1e-9] = 1.0
    w, b = logistic_fit((X_tr - mu) / sd, y_tr)
    prob = 1.0 / (1.0 + np.exp(-((X_te - mu) / sd @ w + b)))
    best = None
    for thr in np.arange(0.05, 0.95, 0.025):
        pred = (prob >= thr).astype(int)
        tp = ((pred == 1) & (y_te == 1)).sum()
        fp = ((pred == 1) & (y_te == 0)).sum()
        fn = ((pred == 0) & (y_te == 1)).sum()
        tn = ((pred == 0) & (y_te == 0)).sum()
        sens = tp / max(1, tp + fn)
        spec = tn / max(1, tn + fp)
        youden = sens + spec - 1
        if best is None or youden > best[0]:
            best = (youden, thr, sens, spec)
    _, thr, sens, spec = best
    metrics.append((thr, sens, spec))

sens = np.mean([m[1] for m in metrics])
spec = np.mean([m[2] for m in metrics])
p(f'===== 全自动上限模拟：逻辑回归（先验+票型+置信度）5折 =====')
p(f'伪造检出率: {sens*100:.1f}%')
p(f'真实正确率: {spec*100:.1f}%')
p(f'综合硬判正确率: {(sens + spec) / 2 * 100:.1f}%')
p()

# ---- 规则方案对比 ----
p(f'===== 规则方案对比（全量200视频） =====')
p(f'{"方案":<44s} {"检出":>7s} {"误报":>7s} {"正确率":>8s}')
def report(label, pred):
    tp = sum(1 for v in videos if v[1] == 1 and pred(v))
    fp = sum(1 for v in videos if v[1] == 0 and pred(v))
    tn = sum(1 for v in videos if v[1] == 0 and not pred(v))
    fn = sum(1 for v in videos if v[1] == 1 and not pred(v))
    p(f'{label:<44s} {tp/y.sum()*100:>6.1f}% {fp/(n-y.sum())*100:>6.1f}% {(tp+tn)/n*100:>7.1f}%')

for t in (0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45):
    report(f'纯CV先验 ≥ {t:.2f}', lambda v, t=t: v[2] >= t)
# 先验+模型否决：先验≥0.55判伪造，但模型3/3无伪造且置信≥95且先验<0.8 → 无伪造
def rule_veto(v):
    if v[2] >= 0.55:
        if v[4] >= 3 and v[5] >= 95 and v[2] < 0.8:
            return False
        return True
    return False
report('先验≥0.55 + 模型高置信否决(3/3无伪造∧conf≥95∧先验<0.8)', rule_veto)
# 先验+模型救回：先验<0.55判无伪造，但模型≥1伪造票且先验≥0.4 → 伪造
def rule_rescue(v):
    if v[2] >= 0.55:
        return True
    if v[3] >= 1 and v[2] >= 0.4:
        return True
    return False
report('先验≥0.55 或 (伪造票≥1 ∧ 先验≥0.4)', rule_rescue)
# 组合：否决+救回
def rule_combo(v):
    if v[2] >= 0.55:
        if v[4] >= 3 and v[5] >= 95 and v[2] < 0.8:
            return False
        return True
    if v[3] >= 1 and v[2] >= 0.4:
        return True
    return False
report('组合：先验主判 + 模型否决 + 模型救回', rule_combo)

with open(os.path.join(BASE, 'output', '_auto_sim.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
