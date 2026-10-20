# -*- coding: utf-8 -*-
"""3对样本评估配置：6/15/22 对，16项提示词，qwen-vl-max，1票。"""
import os
import shutil
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
NUMS = [6, 15, 22]
RUN = os.path.join(BASE, '_eval3')
if os.path.exists(RUN):
    shutil.rmtree(RUN)
os.makedirs(RUN)
for n in NUMS:
    os.link(os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)),
            os.path.join(RUN, 'fake_e%d_on_%d.mp4' % (n, n)))
    os.link(os.path.join(BASE, 'videos', '%d.mp4' % n),
            os.path.join(RUN, '%d.mp4' % n))
print('_eval3 就绪: 6 个视频（3对）')

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_eval3'
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_eval3'
with open(os.path.join(BASE, 'config_eval3.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_eval3.yaml 就绪（模型:', cfg['api']['model'], '）')
