# -*- coding: utf-8 -*-
"""用特征表（可靠单次值）校准物理守卫阈值 + 汇总无时长时代的三目标保护情况。"""
import csv
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from src.preprocessor import (_load_model, _prior_with_model, physical_evidence_score,
                              _PRIOR_MODEL_PATH, _PRIOR_V16_PATH)

new_m = _load_model(_PRIOR_MODEL_PATH)
old_m = _load_model(_PRIOR_V16_PATH)
rows = list(csv.DictReader(open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig')))


def to_res(r):
    t = int(float(r['valid_frames']))
    return {
        'duration': float(r['duration']), 'total_frames': t,
        'face_sharpness_mean': float(r['face_sharp_mean']), 'bg_sharpness_mean': float(r['bg_sharp_mean']),
        'neck_sharpness_mean': float(r['neck_sharp_mean']), 'ratio_mean': float(r['ratio_mean']),
        'ratio_min': float(r['ratio_min']), 'ratio_std': float(r['ratio_std']),
        'face_neck_ratio': float(r['face_neck_ratio']), 'fluctuation': float(r['fluctuation']),
        'blur_frames': float(r['blur_frac']) * t, 'is_global_softening': bool(int(float(r['global_softening']))),
        'occl_edge_ratio': float(r['occl_edge_ratio']), 'occl_edge_ratio_min': float(r['occl_edge_ratio_min']),
        'face_box_jitter': float(r['face_box_jitter']), 'face_size_jitter': float(r['face_size_jitter']),
        'noise_ratio': float(r['noise_ratio']),
    }


recs = []
for r in rows:
    res = to_res(r)
    pn = _prior_with_model(res, new_m) or 0.0
    po = _prior_with_model(res, old_m) or 0.0
    ph = physical_evidence_score(res, new_m)
    recs.append((r['video'], r['label'], max(pn, po), ph))

print('三目标（表值，无时长模型）:')
for v, lb, p, ph in recs:
    if v.rsplit('.', 1)[0] in ('F89', 'F97', 'F99'):
        print(f'  {v}: 融合先验={p:.3f} 物理子分={ph:.2f}')

print()
print('守卫阈值扫描（物理子分≥T → 至少存疑）:')
for T in (0.5, 1.0, 1.5, 2.0):
    f_hit = sum(1 for _, lb, p, ph in recs if lb == 'fake' and ph is not None and ph >= T and p < 0.55)
    r_hit = sum(1 for _, lb, p, ph in recs if lb == 'real' and ph is not None and ph >= T and p < 0.55)
    tgt = sum(1 for v, _, _, ph in recs if ph is not None and ph >= T
              and v.rsplit('.', 1)[0] in ('F89', 'F97', 'F99'))
    print(f'  T={T}: 额外捞回低先验伪造 {f_hit} | 额外误伤低先验真实 {r_hit} | 覆盖三目标 {tgt}/3')
