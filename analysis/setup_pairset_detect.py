# -*- coding: utf-8 -*-
"""配对基准集检测配置：14 有效假脸 + 14 配对真视频，生产路由 + 控方两轮。"""
import os
import shutil
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
RUN = os.path.join(BASE, '_pairbench')
if os.path.exists(RUN):
    shutil.rmtree(RUN)
os.makedirs(RUN)
for n in NUMS:
    os.link(os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n)),
            os.path.join(RUN, 'fake_e%d_on_%d.mp4' % (n, n)))
    os.link(os.path.join(BASE, 'videos', '%d.mp4' % n),
            os.path.join(RUN, '%d.mp4' % n))
print('_pairbench 就绪: %d 个视频（%d 假 + %d 真）' % (len(NUMS) * 2, len(NUMS), len(NUMS)))

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

cfg['videos']['dir'] = './_pairbench'
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_benchprod'
with open(os.path.join(BASE, 'config_benchprod.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

cfg['videos']['prompt'] = cfg['strategy']['prosecutor_prompt']
cfg['output']['dir'] = './output_benchpros'
with open(os.path.join(BASE, 'config_benchpros.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_benchprod.yaml / config_benchpros.yaml 就绪')
