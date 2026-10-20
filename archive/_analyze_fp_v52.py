# -*- coding: utf-8 -*-
"""真实组误报归因：14 个先验≥0.55 的真实视频，逐特征分解新旧模型贡献。"""
import csv
import json
import sys

sys.path.insert(0, r'D:\deepfake')

import numpy as np

from src.preprocessor import _load_model, _prior_with_model
from src.preprocessor import _PRIOR_MODEL_PATH, _PRIOR_V16_PATH

# 特征表（含 16 特征）
rows = list(csv.DictReader(open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig')))
by_video = {r['video']: r for r in rows}

# 融合先验表
fused = {}
with open(r'D:\deepfake\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        fused[row['video'].rsplit('.', 1)[0]] = (row['label'], float(row['prior']))

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


def contributions(r, model):
    """返回 {feature: 加权z贡献} 及 z 总和。"""
    res = to_res(r)
    z_parts = {}
    for name, mu, sd, w in zip(model['features'], model['mu'], model['sd'], model['weights']):
        x = {
            'duration': float(res['duration']),
            'valid_frames': float(res['total_frames']),
            'face_sharp_mean': res['face_sharpness_mean'],
            'bg_sharp_mean': res['bg_sharpness_mean'],
            'neck_sharp_mean': res['neck_sharpness_mean'],
            'ratio_mean': res['ratio_mean'],
            'ratio_min': res['ratio_min'],
            'ratio_std': res['ratio_std'],
            'face_neck_ratio': res['face_neck_ratio'],
            'fluctuation': res['fluctuation'],
            'blur_frac': res['blur_frames'] / max(1, res['total_frames']),
            'global_softening': 1.0 if res['is_global_softening'] else 0.0,
            'occl_edge_ratio': res['occl_edge_ratio'],
            'occl_edge_ratio_min': res['occl_edge_ratio_min'],
            'face_box_jitter': res['face_box_jitter'],
            'face_size_jitter': res['face_size_jitter'],
        }[name]
        sd = sd if sd > 1e-9 else 1.0
        z_parts[name] = w * (x - mu) / sd
    return z_parts


FN_CN = {
    'duration': '时长', 'valid_frames': '有效帧数', 'face_sharp_mean': '面部清晰度',
    'bg_sharp_mean': '背景清晰度', 'neck_sharp_mean': '颈部清晰度',
    'ratio_mean': '面/背清晰比均值', 'ratio_min': '面/背清晰比最低',
    'ratio_std': '面/背比标准差', 'face_neck_ratio': '面/颈清晰比',
    'fluctuation': '清晰度波动', 'blur_frac': '异常帧比例', 'global_softening': '全局柔化',
    'occl_edge_ratio': '遮挡边缘比', 'occl_edge_ratio_min': '遮挡边缘比(最低)',
    'face_box_jitter': '人脸框位移抖动', 'face_size_jitter': '人脸框尺寸抖动',
}

misp = [v for v, (lb, p) in fused.items() if lb == 'real' and p >= 0.55]
print('14 个真实误报:', misp)
print()
print('=== 逐视频归因（新模型贡献前3 + 旧模型贡献前3，正值=推向伪造） ===')
agg_new = {}
agg_old = {}
for v in sorted(misp):
    r = by_video.get(v + '.mp4') or by_video.get(v)
    if r is None:
        print(v, 'feature row missing'); continue
    cn = contributions(r, new_model)
    co = contributions(r, old_model)
    top_n = sorted(cn.items(), key=lambda kv: -kv[1])[:3]
    top_o = sorted(co.items(), key=lambda kv: -kv[1])[:3]
    p_new = _prior_with_model(to_res(r), new_model)
    p_old = _prior_with_model(to_res(r), old_model)
    print(f'{v:>4s} 新先验={p_new:.2f} 旧先验={p_old:.2f} 融合={fused[v][1]:.2f}')
    print(f'     新模型: ' + '; '.join(f'{FN_CN[k]} {x:+.2f}' for k, x in top_n))
    print(f'     旧模型: ' + '; '.join(f'{FN_CN[k]} {x:+.2f}' for k, x in top_o))
    for k, x in top_n:
        agg_new[k] = agg_new.get(k, 0) + 1
    for k, x in top_o:
        agg_old[k] = agg_old.get(k, 0) + 1
print()
print('=== 14 个误报中，各特征进入贡献前3的次数 ===')
print('新模型:', {FN_CN[k]: n for k, n in sorted(agg_new.items(), key=lambda kv: -kv[1])})
print('旧模型:', {FN_CN[k]: n for k, n in sorted(agg_old.items(), key=lambda kv: -kv[1])})
