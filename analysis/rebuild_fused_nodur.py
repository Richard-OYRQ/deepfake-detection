# -*- coding: utf-8 -*-
"""用无时长特征的新旧模型重算 200 视频融合先验表（单次扫描特征，max 融合），
并输出混淆矩阵与 14 误报/三目标的变化对比。"""
import csv
import json
import sys

sys.path.insert(0, r'D:\deepfake')

from src.preprocessor import _load_model, _prior_with_model, _PRIOR_MODEL_PATH, _PRIOR_V16_PATH

rows = list(csv.DictReader(open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig')))

new_model = _load_model(_PRIOR_MODEL_PATH)
old_model = _load_model(_PRIOR_V16_PATH)


def to_res(r):
    total = int(float(r['valid_frames']))
    return {
        'duration': float(r['duration']),
        'total_frames': total,
        'face_sharpness_mean': float(r['face_sharp_mean']),
        'bg_sharpness_mean': float(r['bg_sharp_mean']),
        'neck_sharpness_mean': float(r['neck_sharp_mean']),
        'ratio_mean': float(r['ratio_mean']),
        'ratio_min': float(r['ratio_min']),
        'ratio_std': float(r['ratio_std']),
        'face_neck_ratio': float(r['face_neck_ratio']),
        'fluctuation': float(r['fluctuation']),
        'blur_frames': float(r['blur_frac']) * total,
        'is_global_softening': bool(int(float(r['global_softening']))),
        'occl_edge_ratio': float(r['occl_edge_ratio']),
        'occl_edge_ratio_min': float(r['occl_edge_ratio_min']),
        'face_box_jitter': float(r['face_box_jitter']),
        'face_size_jitter': float(r['face_size_jitter']),
    }


results = []
for r in rows:
    res = to_res(r)
    pn = _prior_with_model(res, new_model)
    po = _prior_with_model(res, old_model)
    results.append((r['video'], r['label'], max(pn or 0, po or 0)))

# 落盘新融合表
with open(r'D:\deepfake\output\stable_prior_table.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['video', 'label', 'prior'])
    w.writeheader()
    for v, lb, p in results:
        w.writerow({'video': v, 'label': lb, 'prior': round(p, 4)})
print('融合表已更新: output/stable_prior_table.csv (无时长特征模型)')

print()
for thr in (0.55, 0.60):
    tp = sum(1 for _, lb, p in results if lb == 'fake' and p >= thr)
    fp = sum(1 for _, lb, p in results if lb == 'real' and p >= thr)
    acc = (tp + (100 - fp)) / 200 * 100
    print(f'thr={thr}: 检出 {tp}% | 误报 {fp}% | 综合 {acc:.1f}%')

print()
print('三目标视频融合先验（无时长 vs 有时长）:')
old_fused = {}
with open(r'D:\deepfake\output\stable_prior_table_v16_backup_20260826.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        old_fused[row['video'].rsplit('.', 1)[0]] = float(row['prior'])
# 有时长版融合表（此前生成的已更新覆盖，用备份老表对比旧模型；这里只给当前值）
for v, lb, p in results:
    if v.rsplit('.', 1)[0] in ('F89', 'F97', 'F99'):
        print(f'  {v}: 当前={p:.3f}')

print()
print('14 个原误报真实视频的当前融合先验:')
misp = {'1', '15', '20', '29', '35', '53', '58', '59', '63', '67', '68', '79', '83', '90'}
for v, lb, p in results:
    if v.rsplit('.', 1)[0] in misp:
        print(f'  {v}: {p:.3f}')
