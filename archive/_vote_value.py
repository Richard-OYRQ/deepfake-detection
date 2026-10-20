# -*- coding: utf-8 -*-
"""离线实验：模型票在 CV 先验之外还有多少决策信息？
特征：cv_prior(无时长融合) / phys_score / agg_vote(旧激进票) / agg_conf(旧激进置信)
标签：200 视频真值。5折CV比较各组合。
注意：agg_vote/agg_conf 来自 8/1、8/3 旧激进运行（带定罪式预处理锚定），
其误报被锚定放大——本实验给出的是"模型票信息量"的乐观上界。"""
import csv
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import numpy as np

from src.preprocessor import (_load_model, _prior_with_model, physical_evidence_score,
                              _PRIOR_MODEL_PATH, _PRIOR_V16_PATH)

new_m = _load_model(_PRIOR_MODEL_PATH)
old_m = _load_model(_PRIOR_V16_PATH)


def parse_v(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


def parse_conf(content):
    import re
    m = re.search(r'置信度[：:]\s*\*{0,2}(\d+)\s*/\s*100', content or '')
    return int(m.group(1)) if m else 0


# 旧激进票（8/1 F组 + 8/3 真实组）
agg = {}
for path in (r'D:\deepfake\output\results_2026-08-01T17-15-49Z.json',
             r'D:\deepfake\output\results_2026-08-03T17-22-47Z.json'):
    r = json.load(open(path, encoding='utf-8'))
    for x in r['results']:
        t = str(x.get('task_name', ''))
        agg[t] = (1 if parse_v(x.get('content')) == '伪造' else 0,
                  parse_conf(x.get('content')))


def logistic_fit(X, y, lr=0.1, epochs=800, l2=0.01):
    n, d = X.shape
    w = np.zeros(d)
    b = 0.0
    for _ in range(epochs):
        z = X @ w + b
        p = 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
        err = p - y
        w -= lr * (X.T @ err / n + l2 * w)
        b -= lr * err.mean()
    return w, b


def cv_eval(feats, y, name, folds=5, seed=42):
    X = np.array(feats, dtype=float)
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(y))
    X, y = X[idx], y[idx]
    sens_list, spec_list = [], []
    for k in range(folds):
        lo, hi = len(y) * k // folds, len(y) * (k + 1) // folds
        mask = np.ones(len(y), dtype=bool)
        mask[lo:hi] = False
        X_tr, y_tr = X[mask], y[mask]
        X_te, y_te = X[~mask], y[~mask]
        mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
        sd[sd < 1e-9] = 1.0
        w, b = logistic_fit((X_tr - mu) / sd, y_tr)
        p = 1.0 / (1.0 + np.exp(-((X_te - mu) / sd @ w + b)))
        best = None
        for thr in np.arange(0.05, 0.95, 0.05):
            pred = (p >= thr).astype(int)
            tp = ((pred == 1) & (y_te == 1)).sum()
            fp = ((pred == 1) & (y_te == 0)).sum()
            fn = ((pred == 0) & (y_te == 1)).sum()
            tn = ((pred == 0) & (y_te == 0)).sum()
            sens = tp / max(1, tp + fn)
            spec = tn / max(1, tn + fp)
            youden = sens + spec - 1
            if best is None or youden > best[0]:
                best = (youden, sens, spec)
        sens_list.append(best[1])
        spec_list.append(best[2])
    print(f'  {name:<34s} 检出={np.mean(sens_list)*100:5.1f}%  真实正确={np.mean(spec_list)*100:5.1f}%  综合={np.mean(sens_list+np.mean(spec_list) if False else []) if False else (np.mean(sens_list)+np.mean(spec_list))/2*100:5.1f}%')


rows = list(csv.DictReader(open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig')))
cv_prior = {}
with open(r'D:\deepfake\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        cv_prior[row['video'].rsplit('.', 1)[0]] = float(row['prior'])

feats_cv, feats_phys, feats_vote, feats_conf = [], [], [], []
y = []
for r in rows:
    k = r['video'].rsplit('.', 1)[0]
    t = int(float(r['valid_frames']))
    res = {
        'total_frames': t,
        'face_sharpness_mean': float(r['face_sharp_mean']), 'bg_sharpness_mean': float(r['bg_sharp_mean']),
        'neck_sharpness_mean': float(r['neck_sharp_mean']), 'ratio_mean': float(r['ratio_mean']),
        'ratio_min': float(r['ratio_min']), 'ratio_std': float(r['ratio_std']),
        'face_neck_ratio': float(r['face_neck_ratio']), 'fluctuation': float(r['fluctuation']),
        'blur_frames': float(r['blur_frac']) * t, 'is_global_softening': bool(int(float(r['global_softening']))),
        'occl_edge_ratio': float(r['occl_edge_ratio']), 'occl_edge_ratio_min': float(r['occl_edge_ratio_min']),
        'face_box_jitter': float(r['face_box_jitter']), 'face_size_jitter': float(r['face_size_jitter']),
        'noise_ratio': float(r['noise_ratio']), 'duration': float(r['duration']),
    }
    ph = physical_evidence_score(res, new_m) or 0.0
    v, c = agg.get(k, (0, 0))
    y.append(1 if r['label'] == 'fake' else 0)
    feats_cv.append([cv_prior.get(k, 0)])
    feats_phys.append([cv_prior.get(k, 0), ph])
    feats_vote.append([cv_prior.get(k, 0), ph, v])
    feats_conf.append([cv_prior.get(k, 0), ph, v, c / 100.0])

print(f'样本 {len(y)}（真实 {y.count(0)} / 伪造 {y.count(1)}）')
y = np.array(y)
cv_eval(feats_cv, y, '仅CV先验')
cv_eval(feats_phys, y, 'CV先验+物理子分')
cv_eval(feats_vote, y, 'CV+物理+旧激进票')
cv_eval(feats_conf, y, 'CV+物理+旧激进票+其置信度')
cv_eval([[v] for _, _, v, _ in [(f[0], f[1], f[2], f[3]) for f in feats_conf]], y, '仅旧激进票')
