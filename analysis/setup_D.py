# -*- coding: utf-8 -*-
"""阶段D实验配置：_pairD 目录（逐视频锚定提示词），1票。"""
import os
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_pairD'
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_D'
with open(os.path.join(BASE, 'config_D.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_D.yaml 就绪')
