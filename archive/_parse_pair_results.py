# -*- coding: utf-8 -*-
"""解析配对样本检测结果。"""
import glob
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for d in ('output_pairprod', 'output_pairpros'):
    files = sorted(glob.glob(r'D:\deepfake\%s\results*.json' % d))
    if not files:
        print(d, ': no results')
        continue
    r = json.load(open(files[-1], encoding='utf-8'))
    print('=' * 25, d, '=' * 25)
    for x in r['results']:
        t = x.get('task_name')
        if x.get('error'):
            print('%s: 失败 %s' % (t, str(x.get('error'))[:60]))
            continue
        content = x.get('content') or ''
        lines = [s.strip() for s in content.splitlines()
                 if any(k in s for k in ('伪造类型判断', '综合置信度', '异常项统计', '最终结论'))]
        print('%s | final=%s | highres=%s' % (t, x.get('final_verdict'), x.get('highres')))
        for s in lines[:3]:
            print('   ', s[:100])
