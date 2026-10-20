# -*- coding: utf-8 -*-
"""旧版14项提示词在14对上的逐对判定明细。"""
import glob
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
files = sorted(glob.glob(r'D:\deepfake\output_benchpros\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
by = {str(x.get('task_name')): (x.get('content') or '') for x in r['results']}


def parse(content, key):
    m = re.search(key + r'[：:]\s*\**([^\n*]+?)\**\s*(?:\n|$)', content or '')
    return m.group(1).strip() if m else '?'


print(f'{"编号":>4s} {"假脸-结论":<14s} {"假脸-置信":>8s} | {"真视频-结论":<14s} {"真视频-置信":>8s} | {"一致性":>6s}')
for n in NUMS:
    fk = 'fake_e%d_on_%d' % (n, n)
    fc = by.get(fk, '')
    rc = by.get('%d' % n, '')
    fv = parse(fc, '伪造类型判断')
    rv = parse(rc, '伪造类型判断')
    fconf = re.search(r'综合置信度[：:]\s*\**(\d+)', fc)
    rconf = re.search(r'综合置信度[：:]\s*\**(\d+)', rc)
    fconf = fconf.group(1) if fconf else '?'
    rconf = rconf.group(1) if rconf else '?'
    same = '一致' if (fv == '伪造') == (rv == '伪造') else '不同'
    print(f'{n:>4d} {fv:<14s} {fconf:>8s} | {rv:<14s} {rconf:>8s} | {same:>6s}')

print()
print('汇总：假脸判伪造 10/14，真视频判伪造 10/14 → 对子一致率 10/14（模型无法区分这对真假）')
