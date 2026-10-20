# -*- coding: utf-8 -*-
"""验证自适应路由的数据结构：
1. 真实组（纯数字）分辨率分布
2. 24 个 CV 误报真实视频的分辨率
3. 伪造组分辨率上限确认
4. 按分辨率分组的 CV 先验分布（各组的存疑/放行情况）"""
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import cv2
import numpy as np

BASE = r'D:\deepfake'


def probe(p):
    cap = cv2.VideoCapture(p)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return w, h


# 1) 真实组（纯数字）分辨率
reals = {}
fake = {}
for f in sorted(os.listdir(os.path.join(BASE, 'videos'))):
    if f.lower().endswith('.mp4') and f.split('.')[0].isdigit():
        reals[f] = probe(os.path.join(BASE, 'videos', f))
for f in sorted(os.listdir(os.path.join(BASE, '待鉴别'))):
    if f.lower().endswith('.mp4'):
        fake[f] = probe(os.path.join(BASE, '待鉴别', f))

print('真实组(纯数字100):')
from collections import Counter
rc = Counter(reals.values())
for (w, h), n in sorted(rc.items(), key=lambda kv: -kv[1]):
    print(f'  {w}x{h}: {n}')
print('伪造组(100):')
fc = Counter(fake.values())
for (w, h), n in sorted(fc.items(), key=lambda kv: -kv[1]):
    print(f'  {w}x{h}: {n}')

# 2) 24 个 CV 误报（无时长表 prior≥0.55）真实视频的分辨率
fp24 = ['68', '63', '29', '89', '67', '98', '65', '74', '93', '20', '15', '72',
        '95', '21', '100', '84', '40', '36', '38', '87', '86', '4', '90', '62']
print()
print('24 个 CV 误报真实视频的分辨率分布:')
fp_res = Counter()
for v in fp24:
    w, h = reals.get(v + '.mp4', (0, 0))
    fp_res[(w, h)] += 1
    # print(f'  {v}.mp4: {w}x{h}')
for (w, h), n in sorted(fp_res.items(), key=lambda kv: -kv[1]):
    print(f'  {w}x{h}: {n} 个')

# 3) 1080P 路由阈值下，两组各有多少进入"模型主导"分支
hi_thr = (1920, 1080)
print()
print(f'路由阈值 ≥{hi_thr[0]}x{hi_thr[1]}（模型主导分支）:')
n_real_hi = sum(1 for (w, h) in reals.values() if w >= hi_thr[0] and h >= hi_thr[1])
n_fake_hi = sum(1 for (w, h) in fake.values() if w >= hi_thr[0] and h >= hi_thr[1])
print(f'  真实组进入: {n_real_hi}/100   伪造组进入: {n_fake_hi}/100')
hi_thr2 = (1280, 720)
print(f'路由阈值 ≥{hi_thr2[0]}x{hi_thr2[1]}:')
n_real_hi2 = sum(1 for (w, h) in reals.values() if w >= hi_thr2[0] and h >= hi_thr2[1])
n_fake_hi2 = sum(1 for (w, h) in fake.values() if w >= hi_thr2[0] and h >= hi_thr2[1])
print(f'  真实组进入: {n_real_hi2}/100   伪造组进入: {n_fake_hi2}/100')
