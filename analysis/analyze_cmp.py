# -*- coding: utf-8 -*-
"""阶段A对比式取证结果分析：换脸段识别准确率 + 差异清单。"""
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
order = json.load(open(os.path.join(BASE, '_paircmp', 'order.json'), encoding='utf-8'))
files = sorted(glob.glob(BASE + r'\output_cmp\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
by = {str(x.get('task_name')): (x.get('content') or '') for x in r['results']}


def parse_choice(content):
    m = re.search(r'换脸版是[：:]\s*\**\s*(片段[AB])', content or '')
    if m:
        return m.group(1)
    # 兜底：找"判断"段中的片段A/B表述
    idx = (content or '').find('### 判断')
    seg = (content or '')[idx:idx + 300] if idx >= 0 else ''
    if '片段B' in seg and '片段A' in seg:
        return None
    m2 = re.search(r'(片段[AB]).*?换脸', seg)
    return m2.group(1) if m2 else None


correct = 0
parsed = 0
unable = 0
print(f'{"对":>4s} {"拼接顺序":>12s} {"模型判断":>8s} {"结果":>6s}')
for k in sorted(order, key=lambda x: order[x]['n']):
    n = order[k]['n']
    real_first = order[k]['real_first']
    truth = '片段B' if real_first else '片段A'  # 假脸所在的真实位置
    c = by.get(k, '')
    choice = parse_choice(c)
    if choice is None:
        unable += 1
        res = '未判断'
    else:
        parsed += 1
        ok = (choice == truth)
        correct += int(ok)
        res = '正确' if ok else '错误'
    print(f'{n:>4d} {"真实在前" if real_first else "假脸在前":>12s} {str(choice):>8s} {res:>6s}')

print()
print(f'可解析判断: {parsed}/14  无法判断: {unable}/14')
print(f'正确: {correct}/14  （随机基线 7/14）')

print()
print('===== 差异清单关键词统计（模型列出的差异类型） =====')
from collections import Counter
types = Counter()
for k, c in by.items():
    in_table = False
    for line in c.splitlines():
        s = line.strip()
        if s.startswith('| # |') or s.startswith('|---'):
            in_table = True
            continue
        if in_table and s.startswith('|'):
            cols = [x.strip() for x in s.split('|')]
            if len(cols) >= 3 and cols[1].isdigit() and cols[2]:
                types[cols[2]] += 1
            elif cols and cols[1] and not cols[1].isdigit():
                break
for t, cnt in types.most_common(12):
    print(f'  {t}: {cnt} 次')
