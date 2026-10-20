# -*- coding: utf-8 -*-
"""阶段D：为28个视频（14对）构建知识注入+CV锚定断言提示词。"""
import io
import os
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from src.preprocessor import analyze_video

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
RUN = os.path.join(BASE, '_pairD')
if os.path.exists(RUN):
    shutil.rmtree(RUN)
os.makedirs(RUN)

TEMPLATE = '''你是一名数字取证核验专家。现代AI换脸（如inswapper类）的典型痕迹是"面部软化"：换脸重绘使人脸区域皮肤纹理细节（毛孔、细纹、胡茬）密度低于同画面的颈部，且在面颈交界处可能存在可见的纹理密度跳变。

请对本视频执行三项核验，每项输出"支持 / 反对 / 无法判定"并附一句理由（注明时间戳）：

【核验一】面颈纹理跳变：面颈交界处是否存在可见的皮肤纹理密度跳变（面部一侧明显更光滑）？
【核验二】面部纹理细节：面部皮肤的毛孔、细纹等微观细节是否明显少于颈部？
【核验三】预处理数据交叉核验：预处理测得本视频面颈清晰度比={ratio}（面部清晰度{face}/颈部清晰度{neck}，真实人脸通常≥0.8）。该量化数据与你对画面的观察是否一致？

## 输出格式
### 核验结果
| # | 核验项 | 结论 | 理由 |
|---|--------|------|------|
| 1 | 面颈纹理跳变 |   |   |
| 2 | 面部纹理细节 |   |   |
| 3 | 预处理数据交叉核验 |   |   |

### 综合观察
（2句话）

## 注意
禁止编造观察；看不清的核验项写"无法判定"，不得猜测。
'''


def anchor_values(p):
    r = analyze_video(p)
    if 'error' in r:
        return None
    face = r.get('face_sharpness_mean', 0)
    neck = r.get('neck_sharpness_mean') or 0
    ratio = r.get('face_neck_ratio')
    if ratio is None and neck > 0:
        ratio = round(face / neck, 2)
    return face, neck, ratio if ratio is not None else -1


count = 0
for n in NUMS:
    for tag, path in (('%d' % n, os.path.join(BASE, 'videos', '%d.mp4' % n)),
                      ('fake_e%d_on_%d' % (n, n),
                       os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))):
        vals = anchor_values(path)
        if vals is None:
            print(tag, 'CV失败，跳过')
            continue
        face, neck, ratio = vals
        prompt = TEMPLATE.format(face=round(face, 1), neck=round(neck, 1), ratio=ratio)
        dst = os.path.join(RUN, tag + '.mp4')
        os.link(path, dst)
        with open(os.path.join(RUN, tag + '.txt'), 'w', encoding='utf-8') as f:
            f.write(prompt)
        count += 1
        print(f'{tag:<16s} 面颈比={ratio:<6} 提示词就绪')
print('共构建', count, '个视频+锚定提示词')
