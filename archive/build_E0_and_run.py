# -*- coding: utf-8 -*-
"""确认实验：①严格对照（无证据图+E提示词，28视频）②稳定性复跑（E配置重跑）。
两个API运行串行执行。"""
import os
import shutil
import subprocess
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from src.preprocessor import analyze_video

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]

# ---- 严格对照：无图版提示词（E提示词去掉证据图部分） ----
E0_TEMPLATE = '''你是一名数字取证核验专家。现代AI换脸（如inswapper类）的典型痕迹是"面部软化"：换脸重绘使面部纹理细节明显少于颈部。请对本视频完成三项核验：

【核验一】热力图对比：请想象将本视频人脸区与颈部区的纹理细节密度分别可视化——面部一侧是否明显比颈部一侧更平滑？
【核验二】剖面曲线：请想象沿面部中线从上到下的纹理细节强度曲线——在面颈分界处是否存在明显的台阶式下降？
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
不要凭印象作答，确实看不出差异就写"无法判定"。
'''


def anchor(p):
    r = analyze_video(p)
    if 'error' in r:
        return ''
    face = r.get('face_sharpness_mean', 0)
    neck = r.get('neck_sharpness_mean') or 0
    ratio = r.get('face_neck_ratio')
    if ratio is None and neck > 0:
        ratio = round(face / neck, 2)
    return '\n（附加量化参考：本视频实测面颈清晰度比=%s，真实人脸通常≥0.8。请核验该数字与你观察的一致性。）' % ratio


RUN0 = os.path.join(BASE, '_pairE0')
if os.path.exists(RUN0):
    shutil.rmtree(RUN0)
os.makedirs(RUN0)
for n in NUMS:
    for tag, path in (('%d' % n, os.path.join(BASE, 'videos', '%d.mp4' % n)),
                      ('fake_e%d_on_%d' % (n, n),
                       os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)))):
        os.link(path, os.path.join(RUN0, tag + '.mp4'))
        with open(os.path.join(RUN0, tag + '.txt'), 'w', encoding='utf-8') as f:
            f.write(E0_TEMPLATE + anchor(path))

# 两个配置
with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_pairE0'
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_E0'
with open(os.path.join(BASE, 'config_E0.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_pairE'
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_E2'
with open(os.path.join(BASE, 'config_E2.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

print('配置就绪，开始串行运行两个实验...')
r1 = subprocess.run([sys.executable, 'main.py', '--config', 'config_E0.yaml'])
print('严格对照完成 exit=%d' % r1.returncode)
r2 = subprocess.run([sys.executable, 'main.py', '--config', 'config_E2.yaml'])
print('稳定性复跑完成 exit=%d' % r2.returncode)
