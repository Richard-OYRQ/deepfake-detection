# -*- coding: utf-8 -*-
"""对照实验：同一拟合代码、同一特征集，在新旧两张表上的5折CV差异。"""
import csv
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np

FIELDS = ['face_sharp_mean', 'bg_sharp_mean', 'neck_sharp_mean',
          'ratio_mean', 'ratio_min', 'ratio_std', 'face_neck_ratio',
          'fluctuation', 'blur_frac', 'global_softening']


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


def cv5(X, y, seed=42, repeat=5):
    sens_list, spec_list = [], []
    for rep in range(repeat):
        rng = np.random.RandomState(seed + rep)
        idx = rng.permutation(len(y))
        Xs, ys = X[idx], y[idx]
        for k in range(5):
            lo, hi = len(y) * k // 5, len(y) * (k + 1) // 5
            mask = np.ones(len(y), dtype=bool)
            mask[lo:hi] = False
            X_tr, y_tr = Xs[mask], ys[mask]
            X_te, y_te = Xs[~mask], ys[~mask]
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
                youden = tp / max(1, tp + fn) + tn / max(1, tn + fp) - 1
                if best is None or youden > best[0]:
                    best = (youden, tp / max(1, tp + fn), tn / max(1, tn + fp))
            sens_list.append(best[1])
            spec_list.append(best[2])
    return np.mean(sens_list), np.std(sens_list), np.mean(spec_list), np.std(spec_list)


for tag, path in (('新表', r'D:\deepfake\output\feature_table.csv'),
                  ('旧表', r'D:\deepfake\output\feature_table_15feat_pure_backup_20260827.csv')):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    rows = sorted(rows, key=lambda r: r['video'])  # 对齐行序，消除排序差异
    X = np.array([[float(r.get(f, 0) or 0) for f in FIELDS] for r in rows])
    y = np.array([1 if r['label'] == 'fake' else 0 for r in rows])
    s, ss, sp, ssp = cv5(X, y, repeat=5)
    print(f'{tag}: 检出 {s*100:.1f}±{ss*100:.1f}%  真实正确 {sp*100:.1f}±{ssp*100:.1f}%')
