# -*- coding: utf-8 -*-
"""阶段E：CV可视化注入——为每个视频生成纹理密度热力图+清晰度剖面图，
与视频拼接（图1 2秒+图2 2秒+视频10秒），让模型"看图读结论"。"""
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'
FFMPEG = r'D:\facefusion\bin\ffmpeg.exe'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
OUT_DIR = os.path.join(BASE, '_pairE')
TMP = os.path.join(BASE, '_pairE_tmp')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TMP, exist_ok=True)


def make_visuals(video_path, tag):
    """生成热力图与剖面图，返回两图路径。"""
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

    # ---- 纹理密度热力图：24px 块内拉普拉斯方差 ----
    bs = 24
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    lap2 = lap * lap
    heat = np.zeros((h // bs + 1, w // bs + 1), dtype=np.float32)
    cnt = np.zeros_like(heat)
    for i in range(0, h - bs, bs):
        for j in range(0, w - bs, bs):
            heat[i // bs, j // bs] += float(lap2[i:i + bs, j:j + bs].mean())
            cnt[i // bs, j // bs] += 1
    heat = np.sqrt(heat / np.maximum(cnt, 1))
    heat = cv2.resize(heat, (w, h), interpolation=cv2.INTER_CUBIC)
    heat_n = (heat - heat.min()) / (heat.max() - heat.min() + 1e-9)
    heat_c = cv2.applyColorMap((heat_n * 255).astype(np.uint8), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(frame, 0.55, heat_c, 0.45, 0)
    # 标注：绿=人脸框，红=颈部框，图例
    cv2.rectangle(overlay, (x, y), (x + fw, y + fh), (0, 255, 0), 4)
    ny1, ny2 = y + fh + int(fh * 0.05), min(h, y + fh + int(fh * 0.9))
    if ny2 > ny1:
        cv2.rectangle(overlay, (x + int(fw * 0.2), ny1), (x + int(fw * 0.8), ny2), (0, 0, 255), 4)
    cv2.putText(overlay, 'GREEN=face  RED=neck  warm=texture  cool=smooth',
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    heat_path = os.path.join(TMP, '%s_heat.jpg' % tag)
    cv2.imwrite(heat_path, overlay, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

    # ---- 面颈清晰度剖面：沿面部中心竖线，每行拉普拉斯方差 ----
    cx = x + fw // 2
    y_top = max(0, y - int(fh * 0.2))
    y_bot = min(h, y + fh + int(fh * 0.9))
    col_band = lap2[y_top:y_bot, max(0, cx - 15):min(w, cx + 15)]
    prof = np.sqrt(col_band.mean(axis=1))
    prof = np.convolve(prof, np.ones(15) / 15, mode='same')
    # 画曲线
    W2, H2 = 960, 540
    canvas = np.full((H2, W2, 3), 255, np.uint8)
    xs = np.linspace(0, W2 - 1, len(prof))
    ys = H2 - 40 - (prof / (prof.max() + 1e-9)) * (H2 - 100)
    pts = np.stack([xs, ys], axis=1).astype(np.int32)
    cv2.polylines(canvas, [pts], False, (0, 0, 255), 3)
    # 人脸框底边位置标记
    fb_rel = (y + fh - y_top) / max(1, (y_bot - y_top))
    fb_x = int(fb_rel * (W2 - 1))
    cv2.line(canvas, (fb_x, 0), (fb_x, H2), (0, 180, 0), 2)
    cv2.putText(canvas, 'FACE', (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 150, 0), 3)
    cv2.putText(canvas, 'NECK', (fb_x + 30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 200), 3)
    cv2.putText(canvas, 'x=top-to-bottom sharpness  green line=face/neck boundary',
                (20, H2 - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 80, 80), 2)
    prof_path = os.path.join(TMP, '%s_prof.jpg' % tag)
    cv2.imwrite(prof_path, canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    return heat_path, prof_path


ok = 0
for n in NUMS:
    for tag, path in (('%d' % n, os.path.join(BASE, 'videos', '%d.mp4' % n)),
                      ('fake_e%d_on_%d' % (n, n),
                       os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))):
        visuals = make_visuals(path, tag)
        if visuals is None:
            print(tag, '无人脸，跳过')
            continue
        heat_path, prof_path = visuals
        out = os.path.join(OUT_DIR, tag + '.mp4')
        cmd = [FFMPEG, '-y',
               '-loop', '1', '-framerate', '30', '-t', '2', '-i', heat_path,
               '-loop', '1', '-framerate', '30', '-t', '2', '-i', prof_path,
               '-i', path,
               '-filter_complex',
               '[0:v]scale=1920:1080,format=yuv420p[h];'
               '[1:v]scale=1920:1080,format=yuv420p[p];'
               '[2:v]trim=duration=10,setpts=PTS-STARTPTS[v];'
               '[h][p][v]concat=n=3:v=1:a=0[out]',
               '-map', '[out]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(tag, 'ffmpeg失败:', r.stderr[-150:])
            continue
        ok += 1
        print(tag, '就绪')
print('共构建', ok, '个可视化拼接视频')
