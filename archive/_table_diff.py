# -*- coding: utf-8 -*-
"""对比新旧两张特征表（同视频同特征）的漂移程度，定位重拟合崩塌原因。"""
import csv
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import numpy as np

A = r'D:\deepfake\output\feature_table.csv'
B = r'D:\deepfake\output\feature_table_15feat_pure_backup_20260827.csv'

ra = {r['video']: r for r in csv.DictReader(open(A, encoding='utf-8-sig'))}
rb = {r['video']: r for r in csv.DictReader(open(B, encoding='utf-8-sig'))}

FEATS = ['face_sharp_mean', 'bg_sharp_mean', 'neck_sharp_mean', 'ratio_mean',
         'ratio_min', 'ratio_std', 'face_neck_ratio', 'fluctuation', 'blur_frac',
         'global_softening', 'occl_edge_ratio', 'face_box_jitter', 'face_size_jitter',
         'noise_ratio']

common = sorted(set(ra) & set(rb))
print(f'共同视频: {len(common)}')
print()
print(f'{"特征":<20s} {"相对漂移(中位|Δ|/旧值)":>20s} {"漂移>50%的视频占比":>22s}')
for f in FEATS:
    deltas = []
    big = 0
    for v in common:
        a = float(ra[v].get(f, 0) or 0)
        b = float(rb[v].get(f, 0) or 0)
        if b == 0:
            continue
        deltas.append(abs(a - b) / abs(b))
        if abs(a - b) / abs(b) > 0.5:
            big += 1
    if deltas:
        print(f'{f:<20s} {np.median(deltas)*100:>18.1f}% {big/len(common)*100:>20.1f}%')
