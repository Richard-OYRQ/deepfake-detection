# -*- coding: utf-8 -*-
"""搭建控方轮校准运行：40 视频（20 CV漏检伪造 + 10 高先验真实 + 10 低先验真实），
生产配置（中性报告+证据图+控方提示词），每视频 1 票。"""
import csv
import os
import shutil
import sys

import yaml

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
RUN_DIR = os.path.join(BASE, '_pcal')

MISSED_FAKES = ['F5', 'F6', 'F7', 'F8', 'F18', 'F19', 'F30', 'F32', 'F33', 'F34',
                'F42', 'F45', 'F46', 'F69', 'F70', 'F76', 'F77', 'F82', 'F92', 'F94']
HIGH_PRIOR_REALS = ['1', '15', '20', '29', '35', '53', '58', '59', '63', '67']

# 低先验真实样本（先验<0.45 中确定性选取 10 个）
prior = {}
with open(os.path.join(BASE, 'output', 'stable_prior_table.csv'), encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        prior[row['video'].rsplit('.', 1)[0]] = float(row['prior'])
low_reals = [v for v, p in sorted(prior.items(), key=lambda kv: kv[1])
             if v.isdigit() and p < 0.45 and v not in HIGH_PRIOR_REALS]
LOW_REALS = low_reals[:10]

videos = ([(v, 'fake') for v in MISSED_FAKES]
          + [(v, 'real') for v in HIGH_PRIOR_REALS]
          + [(v, 'real') for v in LOW_REALS])
print('校准集 %d 视频: 伪造 %d (CV漏检), 真实高先验 %d, 真实低先验 %d' % (
    len(videos), len(MISSED_FAKES), len(HIGH_PRIOR_REALS), len(LOW_REALS)))

if os.path.exists(RUN_DIR):
    shutil.rmtree(RUN_DIR)
os.makedirs(RUN_DIR)
for v, _ in videos:
    src = os.path.join(BASE, '待鉴别', v + '.mp4') if v.startswith('F') \
        else os.path.join(BASE, 'videos', v + '.mp4')
    if not os.path.exists(src):
        print('缺失源文件:', src)
        continue
    os.link(src, os.path.join(RUN_DIR, v + '.mp4'))

# 生成配置：videos.prompt 替换为控方提示词，vote_count=1
with open(os.path.join(BASE, 'config.yaml'), encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
cfg['videos']['dir'] = './_pcal'
cfg['videos']['prompt'] = cfg['strategy']['prosecutor_prompt']
cfg['throttle']['vote_count'] = 1
cfg['output']['dir'] = './output_pcal'
with open(os.path.join(BASE, 'config_pcal.yaml'), 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print('config_pcal.yaml 已生成, 目录:', RUN_DIR)
