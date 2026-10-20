# -*- coding: utf-8 -*-
"""阶段E结果分析：三项核验在真假组的分组统计。"""
import glob
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
files = sorted(glob.glob(BASE + r'\output_E\results*.json'))
if not files:
    print('无结果文件')
    sys.exit(1)
r = json.load(open(files[-1], encoding='utf-8'))
by = {str(x.get('task_name')): (x.get('content') or '') for x in r['results']}
print('结果文件:', files[-1].split('\\')[-1], '| 视频数:', len(by))


def parse_verdicts(content):
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
                elif '无法' in v:
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

print('===== 分组统计（核验1=热力图 核验2=剖面曲线 核验3=视频画面） =====')
for k in ('1', '2', '3'):
    print(f'核验{k}:')
    for vv in ('支持', '反对', '无法判定'):
        f = fake_c.get((k, vv), 0)
        rr = real_c.get((k, vv), 0)
        print(f'  {vv:<6s} 假脸={f:>2d}/14   真视频={rr:>2d}/14')
    print()

print('===== 逐对明细 =====')
print(f'{"对":>4s} {"假脸核1":>8s} {"真核1":>6s} {"假脸核2":>8s} {"真核2":>6s} {"假脸核3":>8s} {"真核3":>6s}')
for n in NUMS:
    fk = 'fake_e%d_on_%d' % (n, n)
    fv = details.get(fk, {})
    rv = details.get('%d' % n, {})
    print(f'{n:>4d} {fv.get("1","?"):>8s} {rv.get("1","?"):>6s} {fv.get("2","?"):>8s} '
          f'{rv.get("2","?"):>6s} {fv.get("3","?"):>8s} {rv.get("3","?"):>6s}')
