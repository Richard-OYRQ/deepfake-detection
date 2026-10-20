# -*- coding: utf-8 -*-
"""
特征判别分析：基于 200 个已标注视频的预处理特征表
1. 逐特征真假分布对比（均值/中位数 + 秩基AUC）
2. 逻辑回归（numpy 实现）5折交叉验证
3. 输出校准报告 + 先验模型 JSON（供 processor 注入提示词）
"""
import csv
import json
import math
import os

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, 'output', 'feature_table.csv')
REPORT_PATH = os.path.join(BASE, 'output', 'feature_analysis.txt')
MODEL_PATH = os.path.join(BASE, 'src', 'prior_model.json')

NUMERIC_FIELDS = [
    'duration', 'valid_frames', 'face_sharp_mean', 'bg_sharp_mean', 'neck_sharp_mean',
    'ratio_mean', 'ratio_min', 'ratio_std', 'face_neck_ratio',
    'fluctuation', 'blur_frac', 'global_softening',
    'occl_edge_ratio', 'occl_edge_ratio_min', 'face_box_jitter', 'face_size_jitter',
]


def load():
    rows = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def auc_rank(x_real, x_fake):
    """秩基 AUC：P(fake > real)，0.5 表示无判别力。"""
    combined = list(x_real) + list(x_fake)
    n_real, n_fake = len(x_real), len(x_fake)
    if n_real == 0 or n_fake == 0:
        return float('nan')
    ranks = {i: r for r, i in enumerate(sorted(range(len(combined)), key=lambda k: combined[k]))}
    sum_ranks_fake = sum(ranks[i] for i in range(n_real, n_real + n_fake))
    auc = (sum_ranks_fake - n_fake * (n_fake + 1) / 2) / (n_real * n_fake)
    return auc


def logistic_fit(X, y, lr=0.1, epochs=500, l2=0.01):
    """简易逻辑回归（梯度下降 + L2）。返回 (weights, bias)。"""
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
    """5折交叉验证，返回平均指标。"""
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
        # 标准化（用训练集统计量）
        mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
        sd[sd < 1e-9] = 1.0
        X_tr_s = (X_tr - mu) / sd
        X_te_s = (X_te - mu) / sd
        w, b = logistic_fit(X_tr_s, y_tr)
        p = 1.0 / (1.0 + np.exp(-(X_te_s @ w + b)))
        # 扫描最优阈值（约登指数）
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
    thr = np.mean([m[0] for m in metrics])
    sens = np.mean([m[1] for m in metrics])
    spec = np.mean([m[2] for m in metrics])
    return thr, sens, spec


def main():
    rows = load()
    real = [r for r in rows if r['label'] == 'real']
    fake = [r for r in rows if r['label'] == 'fake']
    out = []
    def p(line=''):
        out.append(str(line))
        print(line, flush=True)

    p(f'===== 数据概况 =====')
    p(f'真实组: {len(real)} 个, 伪造组: {len(fake)} 个')
    p()

    # ---- 逐特征分析 ----
    p(f'===== 逐特征判别力（秩基AUC, 0.5=无判别力） =====')
    p(f'{"特征":<18s} {"真实均值":>10s} {"伪造均值":>10s} {"AUC":>7s} {"方向":>6s}')
    p('-' * 60)
    aucs = {}
    for field in NUMERIC_FIELDS:
        xr = [float(r[field]) for r in real if r.get(field) not in (None, '', '-1', '-1.0')]
        xf = [float(r[field]) for r in fake if r.get(field) not in (None, '', '-1', '-1.0')]
        if len(xr) < 10 or len(xf) < 10:
            continue
        auc = auc_rank(xr, xf)
        # 用 |auc-0.5| 表示判别力，方向=伪造均值大于真实均值?
        direction = '伪造更高' if np.mean(xf) > np.mean(xr) else '伪造更低'
        p(f'{field:<18s} {np.mean(xr):>10.2f} {np.mean(xf):>10.2f} {auc:>7.3f} {direction:>6s}')
        aucs[field] = abs(auc - 0.5)
    p()

    # ---- 逻辑回归 ----
    p(f'===== 逻辑回归 5折交叉验证 =====')
    usable = [f for f in NUMERIC_FIELDS if f in aucs]
    X = np.array([[float(r.get(f, 0) or 0) for f in usable] for r in rows])
    y = np.array([1 if r['label'] == 'fake' else 0 for r in rows])
    thr, sens, spec = cross_validate(X, y)
    p(f'特征数: {len(usable)}, 样本: {len(rows)}')
    p(f'最优阈值: {thr:.2f}')
    p(f'伪造检出率(敏感性): {sens*100:.1f}%')
    p(f'真实正确率(特异性): {spec*100:.1f}%')
    p()

    # ---- 拟合全量模型并保存 ----
    X_full = X
    mu, sd = X_full.mean(axis=0), X_full.std(axis=0)
    sd[sd < 1e-9] = 1.0
    Xs = (X_full - mu) / sd
    w, b = logistic_fit(Xs, y, epochs=1000)
    p(f'===== 全量模型系数（标准化后） =====')
    coefs = sorted(zip(usable, w.tolist()), key=lambda t: -abs(t[1]))
    for name, c in coefs:
        p(f'  {name:<18s} {c:+.3f}')
    p(f'  bias: {b:+.3f}')

    # 保存先验模型
    model = {
        'features': usable,
        'mu': mu.tolist(),
        'sd': sd.tolist(),
        'weights': w.tolist(),
        'bias': float(b),
        'threshold': float(thr),
        'description': 'P(伪造) = sigmoid(z)，z = Σ w_i*(x_i-mu_i)/sd_i + bias；阈值以上的先验为伪造',
        'cv_sensitivity': round(sens, 3),
        'cv_specificity': round(spec, 3),
    }
    with open(MODEL_PATH, 'w', encoding='utf-8') as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    p(f'先验模型已保存: {MODEL_PATH}')

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))


if __name__ == '__main__':
    main()
