# -*- coding: utf-8 -*-
"""阶段G：耳面结合部区域取证实验。
①单图核验：14对×2视频的耳部裁剪图 → 边缘模糊/伪影核验
②成对对比：同对真耳图+假耳图并排 → 哪张有伪影"""
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

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
client = OpenAI(api_key=cfg['api']['api_key'], base_url=cfg['api']['base_url'],
                timeout=cfg['api']['timeout'])

SINGLE_PROMPT = '''这是一张视频帧的局部裁剪图，显示了人物脸部的耳部与面部结合区域（原生分辨率，未缩放）。AI换脸技术在人脸边缘融合处经常留下痕迹：耳面结合部的边缘模糊、涂抹感、或轻微的伪影。

请只依据这张图片核验：
【核验】耳面结合部边缘是否存在模糊、涂抹或融合伪影？

输出格式：
- 结论：支持（存在伪影）/ 反对（边缘干净）/ 无法判定
- 理由：（一句话）

确实看不出就写"无法判定"，不要猜测。'''

PAIR_PROMPT = '''这是两张视频帧的局部裁剪图（左图和右图），都显示了人物脸部的耳部与面部结合区域。两张图来自内容相同的两段视频，其中一张的人脸经过AI换脸处理。换脸常在人脸边缘融合处（耳面结合部）留下模糊、涂抹或伪影痕迹。

请对比两张图：
【判断】哪张图存在更明显的边缘伪影？左图 / 右图 / 无法判断
【理由】（一句话）

确实看不出就写"无法判断"，不要猜测。'''


def ear_crop(video_path):
    """取最大人脸帧，裁剪耳部区域（脸框左右两侧，原生分辨率）。"""
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
    y1 = max(0, y + int(fh * 0.10))
    y2 = min(h, y + int(fh * 0.70))
    # 左右耳各取一块，取面积更大/边缘内容更丰富的一侧
    crops = []
    for side in (-1, 1):
        bx = x + (fw if side > 0 else 0)
        x1 = max(0, bx - int(fw * 0.55))
        x2 = min(w, bx + int(fw * 0.25))
        if x2 - x1 < 40 or y2 - y1 < 40:
            continue
        crops.append(frame[y1:y2, x1:x2])
    if not crops:
        return None
    return max(crops, key=lambda c: c.shape[0] * c.shape[1])


def encode(img):
    ok, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.tobytes()).decode('ascii')


def ask(messages):
    resp = client.chat.completions.create(
        model=cfg['api']['model'], messages=[{'role': 'user', 'content': messages}],
        max_tokens=600, temperature=cfg['api']['temperature'])
    return resp.choices[0].message.content or ''


def parse_single(content):
    m = None
    for line in (content or '').splitlines():
        if '结论' in line:
            if '支持' in line:
                m = '支持'
            elif '反对' in line:
                m = '反对'
            elif '无法判定' in line:
                m = '无法判定'
    return m


def parse_pair(content):
    if '左图' in content and '右图' not in content.replace('左图', '', 1):
        pass
    for line in (content or '').splitlines():
        if '判断' in line or '哪张' in line:
            if '左图' in line:
                return '左图'
            if '右图' in line:
                return '右图'
    return '无法判断'


crops = {}
for n in PAIRS:
    for tag, path in (('%d' % n, os.path.join(BASE, 'videos', '%d.mp4' % n)),
                      ('fake_e%d_on_%d' % (n, n),
                       os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))):
        c = ear_crop(path)
        if c is not None:
            crops[tag] = c

single_results = {}
print('===== ①单图核验 =====')
for n in PAIRS:
    for tag, grp in (('%d' % n, 'real'), ('fake_e%d_on_%d' % (n, n), 'fake')):
        if tag not in crops:
            print(tag, '裁剪失败')
            continue
        content = ask([{'type': 'image_url', 'image_url': {'url': encode(crops[tag])}},
                       {'type': 'text', 'text': SINGLE_PROMPT}])
        v = parse_single(content)
        single_results[tag] = (grp, v)
        print('%s (%s): %s' % (tag, grp, v), flush=True)
        time.sleep(13)

pair_results = {}
print()
print('===== ②成对对比（左=真 右=假，顺序随机） =====')
import random as _r
_rng = _r.Random(7)
for n in PAIRS:
    rk, fk = '%d' % n, 'fake_e%d_on_%d' % (n, n)
    if rk not in crops or fk not in crops:
        continue
    # 并排拼接（白条分隔）
    a, b = crops[rk], crops[fk]
    hh = max(a.shape[0], b.shape[0])
    a = cv2.copyMakeBorder(a, 0, hh - a.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    b = cv2.copyMakeBorder(b, 0, hh - b.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    sep = np.full((hh, 12, 3), 255, np.uint8)
    joined = np.hstack([a, sep, b])
    if _rng.random() < 0.5:  # 随机交换顺序
        joined = np.hstack([b, sep, a])
        real_side = '右图'
    else:
        real_side = '左图'
    content = ask([{'type': 'image_url', 'image_url': {'url': encode(joined)}},
                   {'type': 'text', 'text': PAIR_PROMPT}])
    v = parse_pair(content)
    ok = None
    if v == '无法判断':
        ok = '未判断'
    elif v == real_side:
        ok = '错误(选了真)'
    else:
        ok = '正确(选了假)'
    pair_results[str(n)] = (v, real_side, ok)
    print('对%s: 模型选%s | 真在%s | %s' % (n, v, real_side, ok), flush=True)
    time.sleep(13)

# 汇总
from collections import Counter
fc, rc = Counter(), Counter()
for tag, (grp, v) in single_results.items():
    (fc if grp == 'fake' else rc)[v] += 1
print()
print('===== 汇总 =====')
print('①单图核验（耳部伪影"支持"）: 假脸=%d/14  真视频=%d/14' % (fc.get('支持', 0), rc.get('支持', 0)))
print('  假脸: 支持%d 反对%d 无法%d | 真: 支持%d 反对%d 无法%d' % (
    fc.get('支持', 0), fc.get('反对', 0), fc.get('无法判定', 0),
    rc.get('支持', 0), rc.get('反对', 0), rc.get('无法判定', 0)))
ok = sum(1 for v in pair_results.values() if v[2] == '正确(选了假)')
print('②成对对比正确率: %d/%d （随机基线≈一半）' % (ok, len(pair_results)))
with open(os.path.join(BASE, 'output', '_stageG_results.json'), 'w', encoding='utf-8') as f:
    json.dump({'single': {k: {'group': v[0], 'verdict': v[1]} for k, v in single_results.items()},
               'pair': pair_results}, f, ensure_ascii=False, indent=2)
print('saved output/_stageG_results.json')
