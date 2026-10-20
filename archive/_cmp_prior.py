# -*- coding: utf-8 -*-
"""对比 pcal 实时先验 vs v52 含时长官方先验。"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

v52 = json.load(open(r'D:\deepfake\output\results_v52_全自动0.55_融合先验_20260826.json', encoding='utf-8'))
by = {x.get('task_name'): x.get('prior_p') for x in v52['results']}
pcal = json.load(open(r'D:\deepfake\output_pcal\results_2026-08-26T14-01-57Z.json', encoding='utf-8'))
print('视频 | v52含时长先验 | pcal实时先验')
for x in pcal['results']:
    t = str(x.get('task_name'))
    print(f'{t:>5s} | {by.get(t)} | {x.get("prior_p")}')
