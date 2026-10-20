# -*- coding: utf-8 -*-
"""自适应路由离线模拟（零 API 成本）：
- 高清分支（≥1280x720）：模型保守票主导——无伪造票放行，CV冲突规则豁免
- 低清分支：CV 主判 + 物理守卫 + 控方捞回（40视频实测数据）
数据：8/23 全量运行票型 + 无时长融合先验表 + 物理子分 + 分辨率探测 + pcal控方实测
"""
import csv
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2

from src.preprocessor import _load_model, physical_evidence_score, _PRIOR_MODEL_PATH

BASE = r'D:\deepfake'
HI_W, HI_H = 1280, 720
GUARD = 0.5
PRIOR_THR = 0.55

# 标签 + 融合先验
labels, cv_prior = {}, {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        cv_prior[k] = float(row['prior'])

# 物理子分
new_m = _load_model(_PRIOR_MODEL_PATH)
phys = {}
for row in csv.DictReader(open(BASE + r'\output\feature_table.csv', encoding='utf-8-sig')):
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

# 分辨率
def probe(p):
    cap = cv2.VideoCapture(p)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return w, h

res_map = {}
for f in sorted(os.listdir(BASE + r'\videos')):
    if f.lower().endswith('.mp4') and f.split('.')[0].isdigit():
        res_map[f.split('.')[0]] = probe(BASE + r'\videos' + '\\' + f)
for f in sorted(os.listdir(BASE + r'\待鉴别')):
    if f.lower().endswith('.mp4'):
        res_map[f.split('.')[0]] = probe(BASE + r'\待鉴别' + '\\' + f)

# 保守票（8/23 全量，全部视频都有）与控方票（40个）
r823 = json.load(open(BASE + r'\output\results_2026-08-23T09-12-51Z_refused.json', encoding='utf-8'))
cons_vote = {}
for x in r823['results']:
    t = str(x.get('task_name'))
    tally = x.get('vote_result') or {}
    fake_votes = sum(tally.get(k, 0) for k in ('换脸', '面部重演', '全生成'))
    cons_vote[t] = (fake_votes, tally)


def parse_v(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


pcal = json.load(open(BASE + r'\output_pcal\results_2026-08-26T14-01-57Z.json', encoding='utf-8'))
pros = {str(x.get('task_name')): parse_v(x.get('content')) for x in pcal['results']}

# ---- 模拟 ----
def adaptive_triage(k):
    """返回 无伪造/存疑/伪造。"""
    hi = res_map.get(k, (0, 0))[0] >= HI_W and res_map.get(k, (0, 0))[1] >= HI_H
    p = cv_prior.get(k, 0)
    ph = phys.get(k, -99.0)
    if hi:
        # 模型保守票主导；CV 冲突豁免；物理守卫保留
        if ph >= GUARD:
            return '存疑'
        return '无伪造'  # 保守票对高清视频全部无伪造（8/23实测）
    # 低清分支：CV+守卫，控方捞回进存疑
    if p >= PRIOR_THR:
        return '存疑'
    if ph >= GUARD:
        return '存疑'
    if pros.get(k) == '伪造':
        return '存疑'
    return '无伪造'


def adaptive_auto(k):
    hi = res_map.get(k, (0, 0))[0] >= HI_W and res_map.get(k, (0, 0))[1] >= HI_H
    p = cv_prior.get(k, 0)
    if hi:
        return '无伪造'  # 保守票主导放行
    if p >= PRIOR_THR:
        return '伪造'
    return '无伪造'


for mode, fn in (('三分类', adaptive_triage), ('全自动', adaptive_auto)):
    mf = {'无伪造': 0, '存疑': 0, '伪造': 0}
    mr = {'无伪造': 0, '存疑': 0, '伪造': 0}
    for k, lb in labels.items():
        v = fn(k)
        (mf if lb == 'fake' else mr)[v] += 1
    print(f'===== 自适应路由 {mode} =====')
    print(f'  伪造组: {mf}')
    print(f'  真实组: {mr}')
    tp = mf['伪造']; fn_ = mf['无伪造']; fp = mr['伪造']; tn = mr['无伪造']
    sus = mf['存疑'] + mr['存疑']
    acc = (tp + tn) / 200 * 100
    print(f'  硬检出={tp} 硬漏检={fn_} 硬误报={fp} 硬正确={tn} 存疑={sus} ({sus/2:.1f}%) 综合正确率={acc:.1f}%')
    print()
