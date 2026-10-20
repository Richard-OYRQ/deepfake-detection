# -*- coding: utf-8 -*-
"""无时长版：重建融合先验表 + 物理证据子分 + 阈值扫描（含守卫规则模拟）。"""
import csv
import sys

sys.path.insert(0, r'D:\deepfake')

import numpy as np

from src.preprocessor import (_PRIOR_MODEL_PATH, _PRIOR_V16_PATH, _load_model,
                              _prior_with_model, physical_evidence_score)

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
        'noise_ratio': float(r['noise_ratio']),
    }


recs = []
for r in rows:
    res = to_res(r)
    pn = _prior_with_model(res, new_model) or 0.0
    po = _prior_with_model(res, old_model) or 0.0
    phys = physical_evidence_score(res, new_model) or float('-inf')
    recs.append((r['video'], r['label'], max(pn, po), pn, po, phys))

# 落盘融合表
with open(r'D:\deepfake\output\stable_prior_table.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['video', 'label', 'prior'])
    w.writeheader()
    for v, lb, p, _, _, _ in recs:
        w.writerow({'video': v, 'label': lb, 'prior': round(p, 4)})
print('融合表已写（无时长模型）')

print()
print('===== 纯先验阈值扫描（无守卫） =====')
for thr in (0.50, 0.55, 0.60, 0.65):
    tp = sum(1 for _, lb, p, *_ in recs if lb == 'fake' and p >= thr)
    fp = sum(1 for _, lb, p, *_ in recs if lb == 'real' and p >= thr)
    print(f'  thr={thr}: 检出 {tp}% | 误报 {fp}% | 综合 {(tp+100-fp)/2:.1f}%')

print()
print('===== 守卫阈值扫描（先验≥0.45 且 物理子分≥T → 伪造） =====')
phys_sorted = sorted(r for r in recs if r[5] > float('-inf'))
for T in (1.0, 1.5, 2.0, 2.5, 3.0):
    tp = sum(1 for _, lb, p, _, _, ph in recs
             if lb == 'fake' and (p >= 0.55 or (p >= 0.45 and ph >= T)))
    fp = sum(1 for _, lb, p, _, _, ph in recs
             if lb == 'real' and (p >= 0.55 or (p >= 0.45 and ph >= T)))
    print(f'  guard_T={T}: 检出 {tp}% | 误报 {fp}% | 综合 {(tp+100-fp)/2:.1f}%')

print()
print('===== 三目标与守卫子分 =====')
for v, lb, p, pn, po, ph in recs:
    if v.rsplit('.', 1)[0] in ('F89', 'F97', 'F99'):
        print(f'  {v}: 融合={p:.3f} 新={pn:.3f} 旧={po:.3f} 物理子分={ph:.2f}')

print()
print('===== 伪造组物理子分分布（校准守卫阈值用） =====')
f_ph = sorted(r[5] for r in recs if r[1] == 'fake' and r[5] > float('-inf'))
r_ph = sorted(r[5] for r in recs if r[1] == 'real' and r[5] > float('-inf'))
for q in (50, 60, 70, 80, 90):
    fi = min(len(f_ph) - 1, int(len(f_ph) * q / 100))
    ri = min(len(r_ph) - 1, int(len(r_ph) * q / 100))
    print(f'  P{q}: 伪造={f_ph[fi]:.2f} 真实={r_ph[ri]:.2f}')
