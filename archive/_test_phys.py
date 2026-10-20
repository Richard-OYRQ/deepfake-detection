# -*- coding: utf-8 -*-
"""临时测试：物理一致性特征的判别力（小样本验证）。
伪造组：F89/F97/F99；真实组：videos/1-20。"""
import os
import sys

sys.path.insert(0, r'D:\deepfake')

import numpy as np

from src.preprocessor import _dense_physical_scan

FAKES = [rf'D:\deepfake\待鉴别\{v}.mp4' for v in ('F89', 'F97', 'F99')]
REALS = [rf'D:\deepfake\videos\{i}.mp4' for i in range(1, 21)]
KEYS = ('occl_edge_ratio', 'occl_edge_ratio_min', 'edge_persist_ratio',
        'face_box_jitter', 'face_size_jitter')


def collect(paths):
    rows = []
    for p in paths:
        name = os.path.splitext(os.path.basename(p))[0]
        try:
            f = _dense_physical_scan(p)
            rows.append((name, f))
            print(f'{name:>5s}  {f}', flush=True)
        except Exception as e:
            print(f'{name:>5s}  ERROR: {e}', flush=True)
    return rows


def rank_auc(rv, fv):
    """P(fake > real)，0.5=无判别力。"""
    if not rv or not fv:
        return float('nan')
    allv = list(rv) + list(fv)
    nr = len(rv)
    ranks = {i: r for r, i in enumerate(sorted(range(len(allv)), key=lambda k: allv[k]))}
    sr = sum(ranks[i] for i in range(nr, nr + len(fv)))
    return (sr - len(fv) * (len(fv) + 1) / 2) / (nr * len(fv))


print('===== 伪造组 =====')
fake_rows = collect(FAKES)
print()
print('===== 真实组 =====')
real_rows = collect(REALS)

print()
print('===== 汇总 =====')
for key in KEYS:
    fv = [f[key] for _, f in fake_rows if key in f]
    rv = [f[key] for _, f in real_rows if key in f]
    if fv and rv:
        auc = rank_auc(rv, fv)
        print(f'{key:<20s} 伪造均值={np.mean(fv):>8.3f} 真实均值={np.mean(rv):>8.3f} '
              f'伪造中位={np.median(fv):>8.3f} 真实中位={np.median(rv):>8.3f} AUC={auc:.2f}')
    else:
        print(f'{key:<20s} 数据不足 fake={len(fv)} real={len(rv)}')
