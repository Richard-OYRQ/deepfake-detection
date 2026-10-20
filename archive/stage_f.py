# -*- coding: utf-8 -*-
"""阶段F：高清静帧实验——原生分辨率人脸+颈部裁剪图（纯图片请求，不走视频管线），
检验模型视觉编码器是否能在高分辨率静帧上感知"面部软化"指纹。"""
import base64
import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2
import yaml
from openai import OpenAI

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'
PAIRS = [3, 5, 6, 8, 10, 14, 15, 22]

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
client = OpenAI(api_key=cfg['api']['api_key'], base_url=cfg['api']['base_url'],
                timeout=cfg['api']['timeout'])

PROMPT = '''这是一张从视频中提取的原生分辨率截图（人脸+颈部区域，未缩放）。现代AI换脸（如inswapper类）的典型痕迹是"面部软化"：换脸重绘使面部皮肤纹理细节（毛孔、细纹）明显少于颈部，且面颈交界处存在可见的纹理密度跳变。

请只依据这张图片完成两项核验，每项输出"支持 / 反对 / 无法判定"并附一句理由：
【核验一】面颈交界处是否存在可见的纹理密度跳变（面部一侧明显更平滑）？
【核验二】面部皮肤的毛孔、细纹等微观细节是否明显少于颈部？

## 输出格式
| # | 核验项 | 结论 | 理由 |
|---|--------|------|------|
| 1 | 面颈纹理跳变 |   |   |
| 2 | 面部纹理细节 |   |   |
确实看不出差异就写"无法判定"，不要猜测。'''


def best_crop(video_path):
    """取最大人脸帧，裁剪人脸+颈部区域（原生分辨率，外扩1.6倍）。"""
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
    cx, cy = x + fw / 2, y + fh / 2
    side = max(fw, fh) * 1.7
    x1, y1 = max(0, int(cx - side / 2)), max(0, int(cy - side / 2))
    x2, y2 = min(w, int(cx + side / 2)), min(h, int(cy + side / 2))
    return frame[y1:y2, x1:x2]


def ask(image, tag):
    ok, buf = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    url = 'data:image/jpeg;base64,' + base64.b64encode(buf.tobytes()).decode('ascii')
    resp = client.chat.completions.create(
        model=cfg['api']['model'],
        messages=[{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': url}},
            {'type': 'text', 'text': PROMPT},
        ]}],
        max_tokens=1200,
        temperature=cfg['api']['temperature'],
    )
    return resp.choices[0].message.content or ''


def parse_verdicts(content):
    out = {}
    for line in (content or '').splitlines():
        s = line.strip()
        if s.startswith('|'):
            cols = [c.strip().strip('*') for c in s.split('|')]
            if len(cols) >= 4 and cols[1].isdigit():
                v = cols[3]
                if '支持' in v:
                    out[cols[1]] = '支持'
                elif '反对' in v:
                    out[cols[1]] = '反对'
                elif '无法' in v:
                    out[cols[1]] = '无法判定'
    return out


results = {}
for n in PAIRS:
    for tag, path, grp in (('%d' % n, os.path.join(BASE, 'videos', '%d.mp4' % n), 'real'),
                           ('fake_e%d_on_%d' % (n, n),
                            os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)),
                            'fake')):
        crop = best_crop(path)
        if crop is None:
            print(tag, '裁剪失败')
            continue
        content = ask(crop, tag)
        results[tag] = (grp, parse_verdicts(content))
        print('%s (%s) 核验: %s' % (tag, grp, parse_verdicts(content)), flush=True)
        time.sleep(13)  # 5 RPM 限速

# 汇总
from collections import Counter
fc, rc = Counter(), Counter()
for tag, (grp, v) in results.items():
    for k, vv in v.items():
        (fc if grp == 'fake' else rc)[(k, vv)] += 1
print()
print('===== 阶段F汇总（8对高清静帧） =====')
for k in ('1', '2'):
    print('核验%s:' % k)
    for vv in ('支持', '反对', '无法判定'):
        print('  %s: 假脸=%d/8  真视频=%d/8' % (vv, fc.get((k, vv), 0), rc.get((k, vv), 0)))
with open(os.path.join(BASE, 'output', '_stageF_results.json'), 'w', encoding='utf-8') as f:
    json.dump({k: {'group': v[0], 'verdicts': v[1]} for k, v in results.items()},
              f, ensure_ascii=False, indent=2)
print('saved output/_stageF_results.json')
