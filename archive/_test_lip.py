# -*- coding: utf-8 -*-
"""唇同步特征小样本验证：3 伪造 + 20 真实。"""
import os
import sys

sys.path.insert(0, r'D:\deepfake')

import numpy as np

from src.preprocessor import _lip_sync_scan

FAKES = [rf'D:\deepfake\待鉴别\{v}.mp4' for v in ('F89', 'F97', 'F99')]
REALS = [rf'D:\deepfake\videos\{i}.mp4' for i in range(1, 21)]


def collect(paths):
    rows = []
    for p in paths:
        name = os.path.splitext(os.path.basename(p))[0]
        try:
            f = _lip_sync_scan(p)
            rows.append((name, f))
            print(f'{name:>5s}  {f}', flush=True)
        except Exception as e:
            print(f'{name:>5s}  ERROR: {e}', flush=True)
    return rows


def rank_auc(rv, fv):
    if not rv or not fv:
        return float('nan')
    allv = list(rv) + list(fv)
    nr = len(rv)
    ranks = {i: q for q, i in enumerate(sorted(range(len(allv)), key=lambda k: allv[k]))}
    sr = sum(ranks[i] for i in range(nr, nr + len(fv)))
    return (sr - len(fv) * (len(fv) + 1) / 2) / (nr * len(fv))


print('===== 伪造组 =====')
fake_rows = collect(FAKES)
print()
print('===== 真实组 =====')
real_rows = collect(REALS)
print()
for key in ('lip_sync_corr', 'lip_sync_lag'):
    fv = [f[key] for _, f in fake_rows if key in f]
    rv = [f[key] for _, f in real_rows if key in f]
    if fv and rv:
        auc = rank_auc(rv, fv)
        print(f'{key:<16s} 伪造均值={np.mean(fv):.3f} 真实均值={np.mean(rv):.3f} '
              f'AUC={auc:.2f} (P(fake>real))')
    else:
        print(f'{key:<16s} 数据不足 fake={len(fv)} real={len(rv)}')
