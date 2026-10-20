# -*- coding: utf-8 -*-
"""3对样本的 CV 评估：15内容特征 + 双先验 + 物理子分。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from src.preprocessor import (analyze_video, _load_model, _prior_with_model,
                              physical_evidence_score, _PRIOR_MODEL_PATH, _PRIOR_V16_PATH)

new_m = _load_model(_PRIOR_MODEL_PATH)
old_m = _load_model(_PRIOR_V16_PATH)

FIELDS = [
    ('face_sharpness_mean', '面部清晰度'), ('bg_sharpness_mean', '背景清晰度'),
    ('neck_sharpness_mean', '颈部清晰度'), ('ratio_mean', '面/背比均值'),
    ('ratio_min', '面/背比最低'), ('ratio_std', '面/背比标准差'),
    ('face_neck_ratio', '面/颈比'), ('fluctuation', '帧间波动'),
    ('blur_frac', '异常帧比例'), ('global_softening', '全局柔化'),
    ('occl_edge_ratio', '遮挡边缘比'), ('occl_edge_ratio_min', '遮挡边缘比最低'),
    ('face_box_jitter', '人脸框位移抖动'), ('face_size_jitter', '人脸框尺寸抖动'),
    ('noise_ratio', '噪声残留比'),
]

VIDEOS = ['fake_e6_on_6', '6', 'fake_e15_on_15', '15', 'fake_e22_on_22', '22']

rows = []
for v in VIDEOS:
    p = os.path.join(r'D:\deepfake\_eval3', v + '.mp4')
    r = analyze_video(p)
    if 'error' in r:
        print(v, 'ERROR:', r.get('error'))
        continue
    total = r.get('total_frames', 1)
    pn = _prior_with_model(r, new_m) or 0.0
    po = _prior_with_model(r, old_m) or 0.0
    ph = physical_evidence_score(r, new_m) or 0.0
    rows.append({
        'video': v,
        'res': r,
        'new_prior': pn,
        'old_prior': po,
        'fused': max(pn, po),
        'phys': ph,
    })

print('===== 逐特征明细 =====')
header = '特征'
for row in rows:
    header += ' | %s' % row['video']
print(header)
for key, cn in FIELDS:
    line = '%s' % cn
    for row in rows:
        val = row['res'].get(key)
        if key == 'blur_frac':
            val = round(row['res'].get('blur_frames', 0) / max(1, row['res'].get('total_frames', 1)), 2)
        if key == 'global_softening':
            val = 1 if row['res'].get('is_global_softening') else 0
        line += ' | %s' % (round(val, 3) if isinstance(val, float) else val)
    print(line)

print()
print('===== 先验与物理子分 =====')
for row in rows:
    print(f"{row['video']:<16s} 新先验={row['new_prior']:.3f} 旧先验={row['old_prior']:.3f} "
          f"融合={row['fused']:.3f} 物理子分={row['phys']:.2f}")
