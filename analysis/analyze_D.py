# -*- coding: utf-8 -*-
"""阶段D结果分析：核验项"支持/反对/无法判定"在真假组的分组统计。"""
import glob
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
files = sorted(glob.glob(BASE + r'\output_D\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
by = {str(x.get('task_name')): (x.get('content') or '') for x in r['results']}


def parse_verdicts(content):
    """解析核验表：{核验编号: 结论}。结论=支持/反对/无法判定。"""
    out = {}
    in_table = False
    for line in (content or '').splitlines():
        s = line.strip()
        if s.startswith('| # |') or s.startswith('|---'):
            in_table = True
            continue
        if in_table and s.startswith('|'):
            cols = [c.strip().strip('*') for c in s.split('|')]
            if len(cols) >= 4 and cols[1].isdigit():
                v = cols[3]
                if '支持' in v:
                    out[cols[1]] = '支持'
                elif '反对' in v:
                    out[cols[1]] = '反对'
                elif '无法判定' in v or '无法' in v:
                    out[cols[1]] = '无法判定'
            elif cols and cols[1] and not cols[1].isdigit():
                break
    return out


from collections import Counter
fake_c, real_c = Counter(), Counter()
details = {}
for n in NUMS:
    for tag, grp in (('%d' % n, 'real'), ('fake_e%d_on_%d' % (n, n), 'fake')):
        v = parse_verdicts(by.get(tag, ''))
        details[tag] = v
        for k, vv in v.items():
            (fake_c if grp == 'fake' else real_c)[(k, vv)] += 1

print('===== 分组统计（14对×3核验项） =====')
for k in ('1', '2', '3'):
    print(f'核验{k}:')
    for vv in ('支持', '反对', '无法判定'):
        f = fake_c.get((k, vv), 0)
        rr = real_c.get((k, vv), 0)
        print(f'  {vv:<6s} 假脸={f:>2d}/14   真视频={rr:>2d}/14')
    print()

print('===== 逐对明细（核验1/2） =====')
print(f'{"对":>4s} {"假脸-核1":>10s} {"真-核1":>8s} {"假脸-核2":>10s} {"真-核2":>8s}')
for n in NUMS:
    fk = 'fake_e%d_on_%d' % (n, n)
    fv = details.get(fk, {})
    rv = details.get('%d' % n, {})
    print(f'{n:>4d} {fv.get("1","?"):>10s} {rv.get("1","?"):>8s} {fv.get("2","?"):>10s} {rv.get("2","?"):>8s}')
