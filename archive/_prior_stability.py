# -*- coding: utf-8 -*-
"""测试无时长模型的先验稳定性：F30 连续 5 次 analyze_video 的先验分布。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from src.preprocessor import (analyze_video, _load_model, _prior_with_model,
                              _PRIOR_MODEL_PATH, _PRIOR_V16_PATH)

new_m = _load_model(_PRIOR_MODEL_PATH)
old_m = _load_model(_PRIOR_V16_PATH)

print('F30 连续 5 次扫描的先验（新模型/旧模型/融合max）:')
for i in range(5):
    res = analyze_video(r'D:\deepfake\待鉴别\F30.mp4')
    if 'error' in res:
        print(f'  run{i+1}: ERROR {res["error"]}')
        continue
    pn = _prior_with_model(res, new_m)
    po = _prior_with_model(res, old_m)
    print(f'  run{i+1}: 新={pn:.3f} 旧={po:.3f} 融合={max(pn or 0, po or 0):.3f} '
          f'| jitter={res.get("face_box_jitter")} size_j={res.get("face_size_jitter")} '
          f'noise={res.get("noise_ratio")} ratio_min={res.get("ratio_min")} '
          f'fluct={res.get("fluctuation")} blur_frac={res.get("blur_frames", 0) / max(1, res.get("total_frames", 1)):.2f}')
