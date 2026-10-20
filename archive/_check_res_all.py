# -*- coding: utf-8 -*-
"""全量 200 视频分辨率/码率分布（按真伪分组）——只读元数据，不解码。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import cv2

BASE = r'D:\deepfake'
groups = {'real': [], 'fake': []}
for d, label in ((os.path.join(BASE, 'videos'), 'real'),
                 (os.path.join(BASE, '待鉴别'), 'fake')):
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv')):
            continue
        p = os.path.join(d, f)
        cap = cv2.VideoCapture(p)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        size_mb = os.path.getsize(p) / 1024 / 1024
        dur = nf / fps
        mbps = size_mb * 8 / dur if dur else 0
        groups[label].append((f, w, h, dur, size_mb, mbps))


def summary(rows, tag):
    import numpy as np
    ws = sorted(set((r[1], r[2]) for r in rows))
    durs = np.array([r[3] for r in rows])
    mbps = np.array([r[5] for r in rows])
    print(f'===== {tag} ({len(rows)} 个) =====')
    print('  分辨率分布:')
    for w, h in ws:
        n = sum(1 for r in rows if r[1] == w and r[2] == h)
        print(f'    {w}x{h}: {n} 个')
    print(f'  时长: 均值 {durs.mean():.1f}s  中位 {np.median(durs):.1f}s')
    print(f'  码率: 均值 {mbps.mean():.1f}Mbps  中位 {np.median(mbps):.1f}Mbps  最低 {mbps.min():.1f}  最高 {mbps.max():.1f}')
    print()


summary(groups['real'], '真实组 videos/')
summary(groups['fake'], '伪造组 待鉴别/')
