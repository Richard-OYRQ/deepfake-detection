# -*- coding: utf-8 -*-
"""阶段E：为可视化拼接视频生成逐视频提示词（证据图解读+三项核验）。"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from src.preprocessor import analyze_video

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
RUN = os.path.join(BASE, '_pairE')

TEMPLATE = '''你是一名数字取证核验专家。本视频由三部分拼接而成：
- 前2秒：纹理密度热力图（暖色=纹理细节多，冷色=平滑；绿色框=人脸区，红色框=颈部区）
- 第2~4秒：面部至颈部的清晰度剖面曲线（横轴=从上到下，纵轴=纹理细节强度；绿线=面颈分界，左半为面部、右半为颈部）
- 第4秒起：待核验的视频画面

现代AI换脸（如inswapper类）的典型痕迹是"面部软化"：换脸重绘使面部纹理细节明显少于颈部。请结合两张证据图，完成三项核验：

【核验一】热力图对比：证据图中人脸区（绿框内）与颈部区（红框内）的暖色程度是否有明显差异？面部一侧是否明显更冷（更平滑）？
【核验二】剖面曲线：剖面曲线在绿线（面颈分界）两侧是否存在明显的台阶式下降（面部一侧曲线更低）？
【核验三】视频画面核验：直接观看视频，面颈交界处是否存在可见的纹理密度跳变？

每项输出"支持 / 反对 / 无法判定"并附一句理由。

## 输出格式
### 核验结果
| # | 核验项 | 结论 | 理由 |
|---|--------|------|------|
| 1 | 热力图对比 |   |   |
| 2 | 剖面曲线 |   |   |
| 3 | 视频画面核验 |   |   |

## 注意
请以证据图的颜色/曲线为判断依据，不要凭印象；确实看不出差异就写"无法判定"。
'''


def anchor(p):
    r = analyze_video(p)
    if 'error' in r:
        return None
    face = r.get('face_sharpness_mean', 0)
    neck = r.get('neck_sharpness_mean') or 0
    ratio = r.get('face_neck_ratio')
    if ratio is None and neck > 0:
        ratio = round(face / neck, 2)
    return face, neck, ratio


count = 0
for n in NUMS:
    for tag, path in (('%d' % n, os.path.join(BASE, 'videos', '%d.mp4' % n)),
                      ('fake_e%d_on_%d' % (n, n),
                       os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))):
        vals = anchor(path)
        note = ''
        if vals is not None:
            face, neck, ratio = vals
            note = '\n（附加量化参考：本视频实测面颈清晰度比=%s，真实人脸通常≥0.8。请核验该数字与证据图是否一致。）' % ratio
        with open(os.path.join(RUN, tag + '.txt'), 'w', encoding='utf-8') as f:
            f.write(TEMPLATE + note)
        count += 1
print('共写入', count, '个提示词文件')
