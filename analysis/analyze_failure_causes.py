# -*- coding: utf-8 -*-
"""v5.4 生产策略下的失败成因列表分析：
A) 伪造未检出：CV漏检26个（含三分类最终硬漏检F39）的逐项归因
B) 真视频认假：CV误伤名单的逐项归因 + 路由分支 + 终裁去向
"""
import csv
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import (_PRIOR_MODEL_PATH, _PRIOR_V16_PATH, _load_model,
                              _prior_with_model, physical_evidence_score)

BASE = r'D:\deepfake'
GUARD = 0.5
PRIOR_THR = 0.55

new_m = _load_model(_PRIOR_MODEL_PATH)
old_m = _load_model(_PRIOR_V16_PATH)

FN_CN = {
    'face_sharp_mean': '面部清晰度', 'bg_sharp_mean': '背景清晰度', 'neck_sharp_mean': '颈部清晰度',
    'ratio_mean': '面/背清晰比均值', 'ratio_min': '面/背清晰比最低', 'ratio_std': '面/背比标准差',
    'face_neck_ratio': '面/颈清晰比', 'fluctuation': '清晰度波动', 'blur_frac': '异常帧比例',
    'global_softening': '全局柔化', 'occl_edge_ratio': '遮挡边缘比', 'occl_edge_ratio_min': '遮挡边缘比最低',
    'face_box_jitter': '人脸框位移抖动', 'face_size_jitter': '人脸框尺寸抖动', 'noise_ratio': '噪声残留比',
}

rows = list(csv.DictReader(open(BASE + r'\output\feature_table.csv', encoding='utf-8-sig')))
labels = {}
cv_prior = {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        cv_prior[k] = float(row['prior'])


def to_res(r):
    t = int(float(r['valid_frames']))
    return {
        'total_frames': t,
        'face_sharpness_mean': float(r['face_sharp_mean']), 'bg_sharpness_mean': float(r['bg_sharp_mean']),
        'neck_sharpness_mean': float(r['neck_sharp_mean']), 'ratio_mean': float(r['ratio_mean']),
        'ratio_min': float(r['ratio_min']), 'ratio_std': float(r['ratio_std']),
        'face_neck_ratio': float(r['face_neck_ratio']), 'fluctuation': float(r['fluctuation']),
        'blur_frames': float(r['blur_frac']) * t, 'is_global_softening': bool(int(float(r['global_softening']))),
        'occl_edge_ratio': float(r['occl_edge_ratio']), 'occl_edge_ratio_min': float(r['occl_edge_ratio_min']),
        'face_box_jitter': float(r['face_box_jitter']), 'face_size_jitter': float(r['face_size_jitter']),
        'noise_ratio': float(r['noise_ratio']), 'duration': float(r['duration']),
    }


def contribs(res, model):
    z_parts = {}
    for name, mu, sd, w in zip(model['features'], model['mu'], model['sd'], model['weights']):
        x = {
            'face_sharp_mean': res['face_sharpness_mean'], 'bg_sharp_mean': res['bg_sharpness_mean'],
            'neck_sharp_mean': res['neck_sharpness_mean'], 'ratio_mean': res['ratio_mean'],
            'ratio_min': res['ratio_min'], 'ratio_std': res['ratio_std'],
            'face_neck_ratio': res['face_neck_ratio'], 'fluctuation': res['fluctuation'],
            'blur_frac': res['blur_frames'] / max(1, res['total_frames']),
            'global_softening': 1.0 if res['is_global_softening'] else 0.0,
            'occl_edge_ratio': res['occl_edge_ratio'], 'occl_edge_ratio_min': res['occl_edge_ratio_min'],
            'face_box_jitter': res['face_box_jitter'], 'face_size_jitter': res['face_size_jitter'],
            'noise_ratio': res['noise_ratio'],
        }[name]
        sd = sd if sd > 1e-9 else 1.0
        z_parts[name] = w * (x - mu) / sd
    return z_parts


phys = {}
feat_store = {}
for r in rows:
    k = r['video'].rsplit('.', 1)[0]
    res = to_res(r)
    feat_store[k] = res
    ph = physical_evidence_score(res, new_m)
    phys[k] = ph if ph is not None else -99.0

# 分辨率
res_map = {}
for d, sel in ((os.path.join(BASE, 'videos'), lambda s: s.isdigit()),
               (os.path.join(BASE, '待鉴别'), lambda s: True)):
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith('.mp4'):
            continue
        stem = f.split('.')[0]
        if not sel(stem):
            continue
        cap = cv2.VideoCapture(os.path.join(d, f))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        res_map[stem] = (w, h)

# 控方数据（40+8）
def parse_v(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


pros = {}
for path in (BASE + r'\output_pcal\results_2026-08-26T14-01-57Z.json',
             BASE + r'\output_pcal2\results_2026-08-26T16-40-33Z.json'):
    r = json.load(open(path, encoding='utf-8'))
    for x in r['results']:
        pros[str(x.get('task_name'))] = parse_v(x.get('content'))

print('=' * 90)
print('A) 伪造未检出分析（当前生产策略）')
print('=' * 90)
missed = sorted(k for k, lb in labels.items()
                if lb == 'fake' and cv_prior.get(k, 0) < PRIOR_THR and phys.get(k, -99.0) < GUARD)
print(f'CV+守卫漏检的伪造共 {len(missed)} 个（全自动口径），其中控方已判伪造 {sum(1 for k in missed if pros.get(k) == "伪造")} 个、'
      f'控方也判无伪造 {sum(1 for k in missed if pros.get(k) == "无伪造")} 个')
print()
print(f'{"视频":>6s} {"先验":>6s} {"物理子分":>8s} {"控方":>6s} {"拉低先验的主要特征（负贡献前2）":<40s}')
for k in missed:
    res = feat_store[k]
    cz = sorted(contribs(res, new_m).items(), key=lambda kv: kv[1])[:2]
    reason = '、'.join(f'{FN_CN[n]}({v:+.2f})' for n, v in cz)
    print(f'{k:>6s} {cv_prior[k]:>6.2f} {phys[k]:>8.2f} {pros.get(k, "未测"):>6s} {reason:<40s}')

print()
print(f'三分类最终硬漏检：'
      f'{sorted(k for k in missed if pros.get(k) != "伪造") or "无"}')

print()
print('=' * 90)
print('B) 真视频认假分析（CV 先验≥0.55 的误伤名单）')
print('=' * 90)
fp = sorted((k for k, lb in labels.items() if lb == 'real' and cv_prior.get(k, 0) >= PRIOR_THR),
            key=lambda k: -cv_prior[k])
print(f'CV 误伤真实视频共 {len(fp)} 个：高清分支（模型票放行）{sum(1 for k in fp if res_map.get(k, (0, 0))[0] >= 1280 and res_map.get(k, (0, 0))[1] >= 720)} 个、'
      f'低清分支 {sum(1 for k in fp if not (res_map.get(k, (0, 0))[0] >= 1280 and res_map.get(k, (0, 0))[1] >= 720))} 个')
print()
print(f'{"视频":>6s} {"分辨率":>10s} {"路由":>6s} {"先验":>6s} {"全自动终裁":>10s} {"推高先验的主要特征（正贡献前3）":<50s}')
for k in fp:
    w, h = res_map.get(k, (0, 0))
    hi = w >= 1280 and h >= 720
    res = feat_store[k]
    cz = sorted(contribs(res, new_m).items(), key=lambda kv: -kv[1])[:3]
    reason = '、'.join(f'{FN_CN[n]}({v:+.2f})' for n, v in cz)
    verdict = '无伪造（模型放行）' if hi else '伪造（硬误报）'
    res_str = f'{w}x{h}'
    print(f'{k:>6s} {res_str:>10s} {"高清" if hi else "低清":>6s} {cv_prior[k]:>6.2f} {verdict:>12s} {reason:<50s}')
