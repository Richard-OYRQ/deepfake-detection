# -*- coding: utf-8 -*-
"""冒烟测试结果检查：CV证据图是否附加、核验行是否输出、终裁是否正确。"""
import glob
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = sorted(glob.glob(r'D:\deepfake\output\results_2026-08-29*.json'))
if not files:
    print('无结果文件')
    sys.exit(1)
r = json.load(open(files[-1], encoding='utf-8'))
print('结果文件:', files[-1].split('\\')[-1])
for x in r['results']:
    t = x.get('task_name')
    err = x.get('error')
    c = x.get('content') or ''
    m = re.search(r'面颈纹理跳变核验[：:]\s*\**\s*(支持|反对|无法判定)', c)
    verify = m.group(1) if m else '未输出'
    n_img_hint = 'CV证据图核验' in c
    print(f'{t:<6s} 终裁={x.get("final_verdict"):<6s} prior={x.get("prior_p")} '
          f'核验行={verify:<6s} 提示词含核验块={n_img_hint} 错误={err}')
