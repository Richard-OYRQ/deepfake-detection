# -*- coding: utf-8 -*-
"""补校准最后4个低清低先验真实（13/56/91/93）的控方证据子分。"""
import os
import shutil
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
V = ['13', '56', '91', '93']

run_dir = os.path.join(BASE, '_pcal3')
if os.path.exists(run_dir):
    shutil.rmtree(run_dir)
os.makedirs(run_dir)
for k in V:
    os.link(os.path.join(BASE, 'videos', k + '.mp4'), os.path.join(run_dir, k + '.mp4'))

with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_pcal3'
cfg['videos']['prompt'] = cfg['strategy']['prosecutor_prompt']
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_pcal3'
with open(os.path.join(BASE, 'config_pcal3.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_pcal3.yaml 就绪:', V)
