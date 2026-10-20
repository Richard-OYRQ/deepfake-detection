# -*- coding: utf-8 -*-
"""配对样本素材准备：
- 源脸：从真实视频 5/8/20 中抽最大人脸帧并裁剪（同一数据集内、来源可控）
- 目标视频：1/4/21（1080P 真实），作为换脸载体
产出 pairset/sources/*.jpg + 记录清单 pairset/plan.json
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

import cv2

from src.preprocessor import _detect_face, _read_frame_at

BASE = r'D:\deepfake'
PAIR = os.path.join(BASE, 'pairset')
os.makedirs(os.path.join(PAIR, 'sources'), exist_ok=True)
os.makedirs(os.path.join(PAIR, 'outputs'), exist_ok=True)

PLAN = [
    # (源视频, 目标视频, 输出名)
    ('5', '1', 'fake_s5_on_1'),
    ('8', '4', 'fake_s8_on_4'),
    ('20', '21', 'fake_s20_on_21'),
]

plan_out = []
for src_v, dst_v, out_name in PLAN:
    src_path = os.path.join(BASE, 'videos', src_v + '.mp4')
    dst_path = os.path.join(BASE, 'videos', dst_v + '.mp4')

    # 找源视频中最大的人脸帧
    cap = cv2.VideoCapture(src_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    dur = total / fps
    best = None  # (面积, 帧, 框)
    for ts in [dur * f for f in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)]:
        got = _read_frame_at(cap, ts)
        if got is None:
            continue
        _, frame = got
        r = _detect_face(frame)
        if r is not None:
            area = r[2] * r[3]
            if best is None or area > best[0]:
                best = (area, frame, r)
    cap.release()
    if best is None:
        print(f'{src_v}: 未找到人脸，跳过')
        continue
    _, frame, (x, y, fw, fh) = best
    # 外扩裁剪并保存
    cx, cy = x + fw / 2, y + fh / 2
    side = int(max(fw, fh) * 2.0)
    x1, y1 = max(0, int(cx - side / 2)), max(0, int(cy - side / 2))
    x2, y2 = min(frame.shape[1], int(cx + side / 2)), min(frame.shape[0], int(cy + side / 2))
    crop = frame[y1:y2, x1:x2]
    out_img = os.path.join(PAIR, 'sources', f'src_{src_v}.jpg')
    cv2.imwrite(out_img, crop, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    print(f'源脸 {src_v} → {out_img} ({crop.shape[1]}x{crop.shape[0]})')

    plan_out.append({
        'source_video': src_v + '.mp4',
        'source_face': f'sources/src_{src_v}.jpg',
        'target_video': dst_path,
        'output': os.path.join(PAIR, 'outputs', out_name + '.mp4'),
        'paired_real': dst_path,
        'note': f'源脸来自 {src_v}.mp4（真实），目标 {dst_v}.mp4（1080P 真实），输出=已知伪造',
    })

with open(os.path.join(PAIR, 'plan.json'), 'w', encoding='utf-8') as f:
    json.dump(plan_out, f, ensure_ascii=False, indent=2)
print('plan.json 已生成，共', len(plan_out), '对')
