# -*- coding: utf-8 -*-
"""阶段E实验配置：_pairE 目录（可视化拼接视频+逐视频提示词），1票。"""
import os
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_pairE'
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_E'
with open(os.path.join(BASE, 'config_E.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_E.yaml 就绪')
