# -*- coding: utf-8 -*-
"""从旧特征表备份重建 12 特征先验模型（v16，用于双先验融合）。
与 analyze_features.py 的拟合逻辑完全一致（确定性梯度下降），
旧表 200 行 → 复现 8/23 的旧模型参数。输出 src/prior_model_v16.json。"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, 'output', 'feature_table_v16_backup_20260826.csv')
MODEL_PATH = os.path.join(BASE, 'src', 'prior_model_v16.json')

FIELDS_V16 = [
    'duration', 'valid_frames', 'face_sharp_mean', 'bg_sharp_mean', 'neck_sharp_mean',
    'ratio_mean', 'ratio_min', 'ratio_std', 'face_neck_ratio',
    'fluctuation', 'blur_frac', 'global_softening',
]


def logistic_fit(X, y, lr=0.1, epochs=1000, l2=0.01):
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


def main():
    rows = list(csv.DictReader(open(CSV_PATH, 'r', encoding='utf-8-sig', newline='')))
    X = np.array([[float(r.get(f, 0) or 0) for f in FIELDS_V16] for r in rows])
    y = np.array([1 if r['label'] == 'fake' else 0 for r in rows])
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd < 1e-9] = 1.0
    Xs = (X - mu) / sd
    w, b = logistic_fit(Xs, y)
    model = {
        'features': FIELDS_V16,
        'mu': mu.tolist(),
        'sd': sd.tolist(),
        'weights': w.tolist(),
        'bias': float(b),
        'description': 'v16 旧模型（12特征，8/23拟合复现），与 v5.2 新模型（16特征）做双先验 max 融合',
    }
    with open(MODEL_PATH, 'w', encoding='utf-8') as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
    print(f'v16 模型已保存: {MODEL_PATH}')
    print('weights:', [round(x, 3) for x in w.tolist()], 'bias:', round(b, 3))


if __name__ == '__main__':
    main()
