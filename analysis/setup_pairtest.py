# -*- coding: utf-8 -*-
"""配对样本检测验证配置：e21 对（假+真），生产路由配置 + 控方配置。"""
import os
import shutil
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
RUN = os.path.join(BASE, '_pair1')
if os.path.exists(RUN):
    shutil.rmtree(RUN)
os.makedirs(RUN)
os.link(os.path.join(BASE, 'pairset', 'outputs', 'fake_e21_on_21.mp4'),
         os.path.join(RUN, 'fake_e21_on_21.mp4'))
os.link(os.path.join(BASE, 'videos', '21.mp4'), os.path.join(RUN, '21.mp4'))

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

# 1) 生产路由配置（高清分支：模型保守票直接终裁）
cfg['videos']['dir'] = './_pair1'
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_pairprod'
with open(os.path.join(BASE, 'config_pairprod.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

# 2) 控方配置（同视频，激进提示词）
cfg['videos']['prompt'] = cfg['strategy']['prosecutor_prompt']
cfg['output']['dir'] = './output_pairpros'
with open(os.path.join(BASE, 'config_pairpros.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('pair 测试配置就绪: _pair1 目录（fake_e21_on_21.mp4 + 21.mp4）')
