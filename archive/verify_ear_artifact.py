# -*- coding: utf-8 -*-
"""验证人工观察：耳面结合部伪影的CV可测量性（14对）。
指标：耳侧边界带（人脸框左右边界±15px）的拉普拉斯方差均值，
与面部内部对比。换脸融合模糊 → 边界带锐度下降。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]


def ear_junction_metrics(video_path):
    """返回 (左边界锐度比, 右边界锐度比)——边界带/面内纹理的拉普拉斯方差比。"""
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    best = None
    for f in (0.3, 0.5, 0.7):
        got = _read_frame_at(cap, dur * f)
        if got is None:
            continue
        _, fr = got
        r = _detect_face(fr)
        if r is not None:
            area = r[2] * r[3]
            if best is None or area > best[0]:
                best = (area, fr, r)
    cap.release()
    if best is None:
        return None
    _, frame, (x, y, fw, fh) = best
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lap2 = cv2.Laplacian(gray, cv2.CV_32F) ** 2
    # 耳部高度带：脸框 15%~65% 高度
    y1 = y + int(fh * 0.15)
    y2 = y + int(fh * 0.65)
    if y2 <= y1:
        return None
    ratios = []
    for side in (-1, 1):  # 左/右边界
        bx = x + (fw if side > 0 else 0)
        x1 = max(0, bx - 18)
        x2 = min(w, bx + 18)
        if x2 <= x1 + 10:
            continue
        band = lap2[y1:y2, x1:x2].mean()
        # 面内参考：脸框中心窄带
        cx1 = x + int(fw * 0.3)
        cx2 = x + int(fw * 0.7)
        interior = lap2[y1:y2, cx1:cx2].mean() + 1e-9
        ratios.append(float(band / interior))
    return ratios if ratios else None


print(f'{"对":>4s} {"真·左耳":>10s} {"假·左耳":>10s} {"真·右耳":>10s} {"假·右耳":>10s} {"假更低?":>8s}')
diffs_l, diffs_r = [], []
for n in NUMS:
    r_real = ear_junction_metrics(os.path.join(BASE, 'videos', '%d.mp4' % n))
    r_fake = ear_junction_metrics(os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))
    if not r_real or not r_fake or len(r_real) < 2 or len(r_fake) < 2:
        print(n, '数据不足')
        continue
    rl, rr = r_real
    fl, fr = r_fake
    dl, dr = fl - rl, fr - rr
    diffs_l.append(dl)
    diffs_r.append(dr)
    both_lower = (dl < 0 and dr < 0)
    print(f'{n:>4d} {rl:>10.2f} {fl:>10.2f} {rr:>10.2f} {fr:>10.2f} {"是" if both_lower else "否":>8s}')

print()
print(f'左耳边界锐度比: 假-真差值 均值={np.mean(diffs_l):+.2f} | 假更低的对数 {sum(1 for d in diffs_l if d < 0)}/{len(diffs_l)}')
print(f'右耳边界锐度比: 假-真差值 均值={np.mean(diffs_r):+.2f} | 假更低的对数 {sum(1 for d in diffs_r if d < 0)}/{len(diffs_r)}')
print(f'双侧均更低的对数: {sum(1 for dl, dr in zip(diffs_l, diffs_r) if dl < 0 and dr < 0)}/{len(diffs_l)}')
