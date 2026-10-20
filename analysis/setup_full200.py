# -*- coding: utf-8 -*-
"""任务三：200集全量实跑留档配置——videos/纯数字100真 + 待鉴别/F100假 → _full200。"""
import os
import shutil
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
RUN = os.path.join(BASE, '_full200')
if os.path.exists(RUN):
    shutil.rmtree(RUN)
os.makedirs(RUN)
n = 0
for f in sorted(os.listdir(os.path.join(BASE, 'videos'))):
    if f.lower().endswith('.mp4') and f.split('.')[0].isdigit():
        os.link(os.path.join(BASE, 'videos', f), os.path.join(RUN, f))
        n += 1
for f in sorted(os.listdir(os.path.join(BASE, '待鉴别'))):
    if f.lower().endswith('.mp4'):
        os.link(os.path.join(BASE, '待鉴别', f), os.path.join(RUN, f))
        n += 1
print('_full200 就绪: %d 个视频（100真+100假）' % n)

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_full200'
cfg['output']['dir'] = './output_full200'
with open(os.path.join(BASE, 'config_full200.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_full200.yaml 就绪（模型:', cfg['api']['model'], '）')
