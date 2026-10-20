# -*- coding: utf-8 -*-
"""临时测试：事件帧提取器本地验证（不调用 API）。"""
import os
import sys

sys.path.insert(0, r'D:\deepfake')

import cv2

from src.preprocessor import extract_event_frames

os.makedirs(r'D:\deepfake\output\_event_debug', exist_ok=True)
for v in ('F89', 'F97', 'F99'):
    p = rf'D:\deepfake\_v3_run\{v}.mp4'
    evs = extract_event_frames(p)
    print(f'{v} -> {len(evs)} 张')
    for i, ev in enumerate(evs, 1):
        print(f'    {i}. {ev["label"]}  t={ev["ts"]:.1f}s  shape={ev["image"].shape}')
        cv2.imwrite(rf'D:\deepfake\output\_event_debug\{v}_{i}.jpg', ev['image'])
