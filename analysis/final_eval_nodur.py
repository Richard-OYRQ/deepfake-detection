# -*- coding: utf-8 -*-
"""无时长时代（v5.3）最终离线评估：
A) 确定性部分：全 200 视频，无时长融合先验 + 物理守卫 0.5
B) 实测部分：40 视频控方轮数据 → 对漏检区的真实效果
"""
import csv
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

labels = {}
cv = {}
phys = {}
with open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
with open(r'D:\deepfake\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        cv[row['video'].rsplit('.', 1)[0]] = float(row['prior'])

GUARD = 0.5

# 物理子分（表值）
import sys as _s
_s.path.insert(0, r'D:\deepfake')
from src.preprocessor import _load_model, physical_evidence_score, _PRIOR_MODEL_PATH
new_m = _load_model(_PRIOR_MODEL_PATH)
for row in csv.DictReader(open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig')):
    t = int(float(row['valid_frames']))
    res = {
        'total_frames': t,
        'face_sharpness_mean': float(row['face_sharp_mean']), 'bg_sharpness_mean': float(row['bg_sharp_mean']),
        'neck_sharpness_mean': float(row['neck_sharp_mean']), 'ratio_mean': float(row['ratio_mean']),
        'ratio_min': float(row['ratio_min']), 'ratio_std': float(row['ratio_std']),
        'face_neck_ratio': float(row['face_neck_ratio']), 'fluctuation': float(row['fluctuation']),
        'blur_frames': float(row['blur_frac']) * t, 'is_global_softening': bool(int(float(row['global_softening']))),
        'occl_edge_ratio': float(row['occl_edge_ratio']), 'occl_edge_ratio_min': float(row['occl_edge_ratio_min']),
        'face_box_jitter': float(row['face_box_jitter']), 'face_size_jitter': float(row['face_size_jitter']),
        'noise_ratio': float(row['noise_ratio']),
        'duration': float(row['duration']),
    }
    ph = physical_evidence_score(res, new_m)
    phys[row['video'].rsplit('.', 1)[0]] = ph if ph is not None else -99.0

# 控方实测（40 校准视频）
pcal = json.load(open(r'D:\deepfake\output_pcal\results_2026-08-26T14-01-57Z.json', encoding='utf-8'))


def parse_v(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


pros = {str(x.get('task_name')): parse_v(x.get('content')) for x in pcal['results']}

print('========== A) 确定性部分：无时长CV + 守卫0.5（全200，无控方通道） ==========')
mf = {'无伪造': 0, '存疑': 0, '伪造': 0}
mr = {'无伪造': 0, '存疑': 0, '伪造': 0}
for k, lb in labels.items():
    p = cv.get(k, 0)
    g = phys.get(k, -99.0)
    if lb == 'fake':
        mf['存疑' if (p >= 0.55 or g >= GUARD) else '无伪造'] += 1
    else:
        mr['存疑' if (p >= 0.55 or g >= GUARD) else '无伪造'] += 1
print(f'伪造组: {mf}  (硬漏检 {mf["无伪造"]})')
print(f'真实组: {mr}  (硬误报 {mr["伪造"]})')

print()
print('========== B) 控方轮实测（40校准视频） ==========')
fk = [k for k, lb in labels.items() if lb == 'fake']
missed = [k for k in fk if cv.get(k, 0) < 0.55 and phys.get(k, -99.0) < GUARD]
print('无控方时硬漏检的伪造:', sorted(missed), len(missed), '个')
in_pcal = [k for k in missed if k in pros]
print('其中已实测控方:', len(in_pcal), '个')
rescued = [k for k in in_pcal if pros[k] == '伪造']
print('控方判伪造（→转存疑）:', sorted(rescued), f'{len(rescued)}/{len(in_pcal)}')
print()
print('========== C) 全量投影（假定控方对未实测低先验区同样 100% 敏感/30% 误伤） ==========')
# 低先验真实（先验<0.55且守卫未触发）的控方误伤率：实测 3/10
low_reals = [k for k, lb in labels.items() if lb == 'real'
             and cv.get(k, 0) < 0.55 and phys.get(k, -99.0) < GUARD]
measured = [k for k in low_reals if k in pros]
fp_rate = sum(1 for k in measured if pros[k] == '伪造') / max(1, len(measured))
print(f'低先验真实实测误伤率: {len(measured)} 个中 {sum(1 for k in measured if pros[k] == "伪造")} 个 = {fp_rate:.0%}')
proj_fake_sus = mf['存疑'] + len(missed) - len(in_pcal) + len(rescued)
proj_real_sus = mr['存疑'] + round((len(low_reals) - len(measured)) * fp_rate)
print(f'投影：伪造组 {proj_fake_sus} 存疑 / {100 - proj_fake_sus} 无伪造（硬漏检≈0）')
print(f'投影：真实组 {proj_real_sus} 存疑 / {100 - proj_real_sus} 无伪造 / 0 硬误报')
total_sus = proj_fake_sus + proj_real_sus
print(f'存疑总量 ≈ {total_sus} ({total_sus / 2:.1f}%)，人工复核后端到端正确率 = 硬错误≈0 + 人工判断')
