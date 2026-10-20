# -*- coding: utf-8 -*-
"""配对样本的控方逐项判定对比：真视频 21 vs 假视频 fake_e21_on_21。"""
import glob
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = sorted(glob.glob(r'D:\deepfake\output_pairpros\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
by = {x.get('task_name'): (x.get('content') or '') for x in r['results']}


def parse_items(content):
    out = {}
    in_table = False
    for line in content.splitlines():
        s = line.strip()
        if s.startswith('| # |') or s.startswith('|---'):
            in_table = True
            continue
        if in_table and s.startswith('|'):
            cols = [c.strip() for c in s.split('|')]
            if len(cols) >= 4 and cols[1].isdigit():
                out[cols[1]] = cols[3].strip().strip('*').strip()
            elif cols and cols[1] and not cols[1].isdigit():
                break
    return out


real_items = parse_items(by['21'])
fake_items = parse_items(by['fake_e21_on_21'])
print('项  | 真实21   | 假fake_e21 | 差异')
for i in range(1, 15):
    ri = real_items.get(str(i), '?')
    fi = fake_items.get(str(i), '?')
    mark = ' <-- 差异' if ri != fi else ''
    print(f'{i:>2}  | {ri:<6s} | {fi:<6s}{mark}')
