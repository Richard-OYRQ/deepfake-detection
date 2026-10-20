# -*- coding: utf-8 -*-
"""搭建证据分析师校准运行：40 视频（同 _pcal 目录），分析师提示词 + 思考模式，1票。"""
import os
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
with open(os.path.join(BASE, 'prompts', 'evidence_analyst.md'), encoding='utf-8') as f:
    analyst_prompt = f.read()

cfg['videos']['dir'] = './_pcal'
cfg['videos']['prompt'] = analyst_prompt
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_analyst'
cfg['api']['enable_thinking'] = True
with open(os.path.join(BASE, 'config_analyst.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_analyst.yaml 已生成（思考模式开启，分析师提示词，40视频）')
