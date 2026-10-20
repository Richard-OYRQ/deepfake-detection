# -*- coding: utf-8 -*-
"""时长特征去偏：去掉 duration 重新拟合两个先验模型（零拟合算法改动）。
- 新模型（16特征 → 15特征）→ src/prior_model.json
- 旧模型 v16（12特征 → 11特征）→ src/prior_model_v16.json
拟合算法与 analyze_features.py 完全一致（确定性梯度下降 + L2）。
原模型备份到 src/prior_model_*_with_duration_backup.json。
"""
import csv
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, 'output', 'feature_table.csv')

FIELDS_NEW = [
    'face_sharp_mean', 'bg_sharp_mean', 'neck_sharp_mean',
    'ratio_mean', 'ratio_min', 'ratio_std', 'face_neck_ratio',
    'fluctuation', 'blur_frac', 'global_softening',
    'occl_edge_ratio', 'occl_edge_ratio_min', 'face_box_jitter', 'face_size_jitter',
    'noise_ratio',
]
FIELDS_OLD = [
    'face_sharp_mean', 'bg_sharp_mean', 'neck_sharp_mean',
    'ratio_mean', 'ratio_min', 'ratio_std', 'face_neck_ratio',
    'fluctuation', 'blur_frac', 'global_softening',
]


def logistic_fit(X, y, lr=0.1, epochs=500, l2=0.01):
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


def cross_validate(X, y, folds=5, seed=42):
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(y))
    X, y = X[idx], y[idx]
    metrics = []
    for k in range(folds):
        lo, hi = len(y) * k // folds, len(y) * (k + 1) // folds
        mask = np.ones(len(y), dtype=bool)
        mask[lo:hi] = False
        X_tr, y_tr = X[mask], y[mask]
        X_te, y_te = X[~mask], y[~mask]
        mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
        sd[sd < 1e-9] = 1.0
        X_tr_s = (X_tr - mu) / sd
        X_te_s = (X_te - mu) / sd
        w, b = logistic_fit(X_tr_s, y_tr)
        p = 1.0 / (1.0 + np.exp(-(X_te_s @ w + b)))
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
                best = (youden, thr, sens, spec)
        _, thr, sens, spec = best
        metrics.append((thr, sens, spec))
    return (np.mean([m[0] for m in metrics]),
            np.mean([m[1] for m in metrics]),
            np.mean([m[2] for m in metrics]))


def fit_and_save(rows, fields, model_path, tag):
    X = np.array([[float(r.get(f, 0) or 0) for f in fields] for r in rows])
    y = np.array([1 if r['label'] == 'fake' else 0 for r in rows])
    thr, sens, spec = cross_validate(X, y)
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd < 1e-9] = 1.0
    Xs = (X - mu) / sd
    w, b = logistic_fit(Xs, y, epochs=1000)
    # 备份原模型
    backup = model_path.replace('.json', '_with_duration_backup.json')
    if os.path.exists(model_path) and not os.path.exists(backup):
        shutil.copy2(model_path, backup)
        print('backup:', backup)
    model = {
        'features': fields,
        'mu': mu.tolist(),
        'sd': sd.tolist(),
        'weights': w.tolist(),
        'bias': float(b),
        'threshold': float(thr),
        'description': f'{tag}（已去时长特征，2026-08-26 去偏重拟合）',
        'cv_sensitivity': round(sens, 3),
        'cv_specificity': round(spec, 3),
    }
    with open(model_path, 'w', encoding='utf-8') as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    print(f'{tag}: 5折CV 检出={sens*100:.1f}% 真实正确={spec*100:.1f}% 阈值={thr:.2f} → {model_path}')
    return model


def main():
    rows = list(csv.DictReader(open(CSV_PATH, 'r', encoding='utf-8-sig', newline='')))
    print(f'样本: {len(rows)} (real {sum(1 for r in rows if r["label"]=="real")}, '
          f'fake {sum(1 for r in rows if r["label"]=="fake")})')
    fit_and_save(rows, FIELDS_NEW, os.path.join(BASE, 'src', 'prior_model.json'),
                 '新模型 15特征')
    fit_and_save(rows, FIELDS_OLD, os.path.join(BASE, 'src', 'prior_model_v16.json'),
                 '旧模型 v16 11特征')


if __name__ == '__main__':
    main()
