# -*- coding: utf-8 -*-
"""策略一+三：软化差分热力图生成与"历史参照vs待测"核验实验。
- 1a：为14对生成差分热力图（假脸纹理密度 - 真视频纹理密度，蓝=假脸更平滑）
- 1b：28个图片请求（14正例=真vs假差分图，14对照=真vs真不同片段差分图）"""
import base64
import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import numpy as np
import yaml
from openai import OpenAI

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'
PAIRS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
OUT = os.path.join(BASE, 'output', 'diffmaps')
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
client = OpenAI(api_key=cfg['api']['api_key'], base_url=cfg['api']['base_url'],
                timeout=cfg['api']['timeout'])


def texture_density(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lap2 = cv2.Laplacian(gray, cv2.CV_32F) ** 2
    h, w = gray.shape
    bs = 24
    hh, ww = h // bs + 1, w // bs + 1
    heat = np.zeros((hh, ww), np.float32)
    for i in range(0, h - bs, bs):
        for j in range(0, w - bs, bs):
            heat[i // bs, j // bs] = float(lap2[i:i + bs, j:j + bs].mean())
    heat = np.sqrt(heat)
    return cv2.resize(heat, (w, h), interpolation=cv2.INTER_CUBIC)


def frame_at(video_path, frac=0.5):
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    got = _read_frame_at(cap, (total / fps) * frac)
    cap.release()
    return got[1] if got else None


def diff_map(f1, f2, rect, shared_scale):
    """差分图（蓝=待测更平滑），用配对共享的绝对尺度（近零差异→近灰图）。"""
    h, w = f1.shape[:2]
    d = texture_density(f1) - texture_density(f2)
    dn = np.clip(d / max(shared_scale, 1e-6), -1.0, 1.0)
    vis = np.zeros((h, w, 3), np.uint8)
    neg = np.clip(-dn, 0, 1)
    pos = np.clip(dn, 0, 1)
    vis[:, :, 0] = (neg * 255).astype(np.uint8)  # B通道=更平滑(蓝)
    vis[:, :, 2] = (pos * 255).astype(np.uint8)  # R通道=更锐利(红)
    vis = cv2.addWeighted(f1, 0.45, vis, 0.55, 0)
    if rect is not None:
        x, y, fw, fh = rect
        cv2.rectangle(vis, (x, y), (x + fw, y + fh), (0, 255, 0), 4)
    cv2.putText(vis, 'BLUE=softer than ref  RED=sharper than ref  GREEN=face',
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    return vis


PROMPT = '''这是一张"纹理密度差分图"：它显示待测视频与人物的历史真实视频相比，面部纹理细节密度的差异。蓝色=待测视频该处纹理明显更稀疏（面部软化），红色=更锐利，绿色框=人脸区域。如果两段视频纹理几乎相同，差分图会接近全灰（无明显蓝色或红色）。

现代AI换脸（如inswapper类）的典型痕迹是面部软化：换脸重绘使面部纹理细节明显少于本人的真实视频。请核验：

【核验】绿色人脸框内是否存在明显且集中于面部的蓝色区域（即待测视频面部比历史参照更平滑）？若图像接近全灰或框内蓝红混杂，请如实回答"反对"或"无法判定"。

输出格式：
- 结论：支持（框内蓝色主导）/ 反对（非蓝色主导）/ 无法判定
- 理由：（一句话）'''


def encode(img):
    ok, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.tobytes()).decode('ascii')


def ask(img):
    resp = client.chat.completions.create(
        model=cfg['api']['model'],
        messages=[{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': encode(img)}},
            {'type': 'text', 'text': PROMPT},
        ]}],
        max_tokens=600, temperature=cfg['api']['temperature'])
    return resp.choices[0].message.content or ''


def parse_v(content):
    for line in (content or '').splitlines():
        if '结论' in line:
            if '支持' in line:
                return '支持'
            if '反对' in line:
                return '反对'
            if '无法判定' in line:
                return '无法判定'
    return '?'

# ---- 1a: 生成差分图（修正版：同时间戳近零对照 + 配对共享尺度） ----
print('===== 1a 生成差分热力图（修正版） =====')
cases = []
for n in PAIRS:
    real = os.path.join(BASE, 'videos', '%d.mp4' % n)
    fake = os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n))
    fr = frame_at(real, 0.5)
    ff = frame_at(fake, 0.5)
    # 对照：真视频同一时刻±0.05s（近零差异）
    fr2 = frame_at(real, 0.55)
    if fr is None or ff is None or fr2 is None:
        print(n, '帧提取失败')
        continue
    # 共享尺度：正例与控制差分图的联合最大绝对值
    d_sig = texture_density(ff) - texture_density(fr)
    d_ctrl = texture_density(fr2) - texture_density(fr)
    shared = max(abs(d_sig).max(), abs(d_ctrl).max(), 1e-6)
    r = _detect_face(fr)
    img = diff_map(ff, fr, r, shared)
    ctrl = diff_map(fr2, fr, r, shared)
    path = os.path.join(OUT, 'diff_%d.jpg' % n)
    cpath = os.path.join(OUT, 'ctrl_%d.jpg' % n)
    cv2.imwrite(path, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cv2.imwrite(cpath, ctrl, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    cases.append((n, path, cpath))
    print(n, '就绪')

# ---- 1b: 模型核验 ----
print()
print('===== 1b 模型核验 =====')
results = {}
for n, path, cpath in cases:
    img = cv2.imread(path)
    content = ask(img)
    v = parse_v(content)
    results[n] = {'case': 'fake-vs-real', 'verdict': v}
    print('对%d 正例: %s' % (n, v), flush=True)
    time.sleep(13)
    if cpath:
        cimg = cv2.imread(cpath)
        ccontent = ask(cimg)
        cv = parse_v(ccontent)
        results['ctrl%d' % n] = {'case': 'real-vs-real', 'verdict': cv}
        print('对%d 对照: %s' % (n, cv), flush=True)
        time.sleep(13)

from collections import Counter
pos, ctr = Counter(), Counter()
for k, v in results.items():
    (pos if v['case'] == 'fake-vs-real' else ctr)[v['verdict']] += 1
print()
print('===== 汇总 =====')
print('正例(假vs真): 支持%d 反对%d 无法%d / %d' % (
    pos.get('支持', 0), pos.get('反对', 0), pos.get('无法判定', 0), len(pos)))
print('对照(真vs真): 支持%d 反对%d 无法%d / %d' % (
    ctr.get('支持', 0), ctr.get('反对', 0), ctr.get('无法判定', 0), len(ctr)))
with open(os.path.join(BASE, 'output', '_diffmap_results.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('saved output/_diffmap_results.json')
