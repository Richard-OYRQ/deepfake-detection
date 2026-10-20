# -*- coding: utf-8 -*-
"""阶段A对比式取证实验配置：14个拼接视频，对比专家提示词，1票。"""
import os
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
with open(os.path.join(BASE, 'prompts', 'compare_expert.md'), encoding='utf-8') as f:
    prompt = f.read()

cfg['videos']['dir'] = './_paircmp'
cfg['videos']['prompt'] = prompt
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_cmp'
with open(os.path.join(BASE, 'config_cmp.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_cmp.yaml 就绪')
