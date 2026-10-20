# -*- coding: utf-8 -*-
"""两项零成本验证：
①边界之字率（三区域）200集全表提取 + AUC
②软化系四特征 14对方向一致性"""
import csv
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at, analyze_video

BASE = r'D:\deepfake'


def zigzag_rate(band):
    grad = np.abs(np.diff(band, axis=1))
    pos = np.argmax(grad, axis=1).astype(np.float32)
    steps = np.diff(pos)
    s = steps[steps != 0]
    if len(s) < 10:
        return 0.0
    signs = np.sign(s)
    return float((signs[1:] != signs[:-1]).mean())


def video_zigzag(path, interval=0.4):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    vals = []
    ts = 0.1
    while ts < dur - 0.1:
        got = _read_frame_at(cap, ts)
        if got is not None:
            _, fr = got
            r = _detect_face(fr)
            if r is not None:
                x, y, fw, fh = r
                h, w = fr.shape[:2]
                gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.float32)
                y1, y2 = y + int(fh * 0.15), y + int(fh * 0.75)
                row = []
                if y2 - y1 >= 30:
                    for side in (-1, 1):
                        bx = x + (fw if side > 0 else 0)
                        x1, x2 = max(0, bx - 20), min(w, bx + 20)
                        if x2 - x1 >= 20:
                            row.append(zigzag_rate(gray[y1:y2, x1:x2]))
                    yy1 = y + int(fh * 0.85)
                    yy2 = min(h, y + fh + int(fh * 0.2))
                    if yy2 - yy1 >= 20:
                        x1 = max(0, x - int(fw * 0.15))
                        x2 = min(w, x + fw + int(fw * 0.15))
                        row.append(zigzag_rate(gray[yy1:yy2, x1:x2].T))
                    if len(row) == 3:
                        vals.append(row)
        ts += interval
    cap.release()
    if len(vals) < 5:
        return None
    return np.array(vals).mean(axis=0)


def rank_auc(xr, xf):
    if len(xr) < 10 or len(xf) < 10:
        return float('nan')
    allv = list(xr) + list(xf)
    nr = len(xr)
    ranks = {i: q for q, i in enumerate(sorted(range(len(allv)), key=lambda k: allv[k]))}
    sr = sum(ranks[i] for i in range(nr, nr + len(xf)))
    return (sr - len(xf) * (len(xf) + 1) / 2) / (nr * len(xf))


# ===== ① 200集之字率 =====
print('===== ① 边界之字率 200集 =====')
rows = []
for d, sel, label in ((os.path.join(BASE, 'videos'), lambda s: s.isdigit(), 'real'),
                      (os.path.join(BASE, '待鉴别'), lambda s: True, 'fake')):
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith('.mp4'):
            continue
        stem = f.split('.')[0]
        if not sel(stem):
            continue
        m = video_zigzag(os.path.join(d, f))
        if m is not None:
            rows.append((f, label, m[0], m[1], m[2]))
            print('.', end='', flush=True)
print()
with open(os.path.join(BASE, 'output', 'zigzag_table.csv'), 'w', encoding='utf-8-sig', newline='') as fo:
    w = csv.writer(fo)
    w.writerow(['video', 'label', 'zig_left', 'zig_right', 'zig_jaw'])
    w.writerows([(r[0], r[1], round(r[2], 4), round(r[3], 4), round(r[4], 4)) for r in rows])
reals = [r for r in rows if r[1] == 'real']
fakes = [r for r in rows if r[1] == 'fake']
print('提取: %d 真 + %d 假' % (len(reals), len(fakes)))
for i, name in enumerate(('左边界', '右边界', '下颌线')):
    xr = [r[2 + i] for r in reals]
    xf = [r[2 + i] for r in fakes]
    a = rank_auc(xr, xf)
    print('  %s: 真均值=%.3f 假均值=%.3f AUC=%.3f (P(fake>real)) |AUC-0.5|=%.3f'
          % (name, np.mean(xr), np.mean(xf), a, abs(a - 0.5)))

# ===== ② 软化系 14对 =====
print()
print('===== ② 软化系四特征 14对方向一致性 =====')
PAIRS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
FEATS = [('face_sharpness_mean', '面部清晰度'), ('ratio_mean', '面/背比均值'),
         ('face_neck_ratio', '面/颈比'), ('noise_ratio', '噪声残留比')]
# 真视频特征从特征表取
table = {}
with open(os.path.join(BASE, 'output', 'feature_table.csv'), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        table[r['video'].rsplit('.', 1)[0]] = r
dirs = {}
for n in PAIRS:
    fake_res = analyze_video(os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))
    if 'error' in fake_res:
        print(n, '假脸分析失败')
        continue
    r = table.get('%d' % n)
    if r is None:
        print(n, '真特征缺失')
        continue
    for key, cn in FEATS:
        rv = float(r.get(key, 0) or 0)
        fv = fake_res.get(key, 0) or 0
        if rv == 0 or fv == 0:
            continue
        dirs.setdefault(cn, []).append(1 if fv < rv else 0)
for cn, vals in dirs.items():
    print('  %s: 假更低 %d/%d 对' % (cn, sum(vals), len(vals)))
