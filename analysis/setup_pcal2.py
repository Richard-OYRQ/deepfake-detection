# -*- coding: utf-8 -*-
"""补校准：当前26个低清漏检伪造中未校准的8个，控方轮补跑（生产配置）。"""
import csv
import json
import os
import shutil
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
GUARD = 0.5

# 当前融合先验 + 物理子分
labels, cv = {}, {}
with open(os.path.join(BASE, 'output', 'stable_prior_table.csv'), encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        cv[k] = float(row['prior'])

sys.path.insert(0, BASE)
from src.preprocessor import _load_model, physical_evidence_score, _PRIOR_MODEL_PATH
new_m = _load_model(_PRIOR_MODEL_PATH)
phys = {}
for row in csv.DictReader(open(os.path.join(BASE, 'output', 'feature_table.csv'), encoding='utf-8-sig')):
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
        'noise_ratio': float(row['noise_ratio']), 'duration': float(row['duration']),
    }
    ph = physical_evidence_score(res, new_m)
    phys[row['video'].rsplit('.', 1)[0]] = ph if ph is not None else -99.0

miss = sorted(k for k, lb in labels.items()
              if lb == 'fake' and cv.get(k, 0) < 0.55 and phys.get(k, -99.0) < GUARD)
print('当前漏检伪造:', len(miss), miss)

# 已校准的18个
pcal = json.load(open(os.path.join(BASE, 'output_pcal', 'results_2026-08-26T14-01-57Z.json'), encoding='utf-8'))
calibrated = {str(x.get('task_name')) for x in pcal['results']}
todo = [k for k in miss if k not in calibrated]
print('待补跑:', len(todo), todo)

# 建目录（硬链接）与配置
run_dir = os.path.join(BASE, '_pcal2')
if os.path.exists(run_dir):
    shutil.rmtree(run_dir)
os.makedirs(run_dir)
for k in todo:
    src = os.path.join(BASE, '待鉴别', k + '.mp4')
    os.link(src, os.path.join(run_dir, k + '.mp4'))

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_pcal2'
cfg['videos']['prompt'] = cfg['strategy']['prosecutor_prompt']
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_pcal2'
with open(os.path.join(BASE, 'config_pcal2.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_pcal2.yaml 就绪')
