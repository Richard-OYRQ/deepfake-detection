# -*- coding: utf-8 -*-
"""校准运行分析：控方轮（生产配置）在 CV 漏检区的真实检出/误报。"""
import csv
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
r = json.load(open(BASE + r'\output_pcal\results_2026-08-26T14-01-57Z.json', encoding='utf-8'))

# 真值 + 单次扫描融合先验（无时长表）
labels, table_prior = {}, {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        table_prior[k] = float(row['prior'])


def parse_v(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


def parse_conf(content):
    import re
    m = re.search(r'置信度[：:]\s*\*{0,2}(\d+)\s*/\s*100', content or '')
    return int(m.group(1)) if m else 0


rows = []
for x in r['results']:
    t = str(x.get('task_name', ''))
    rows.append({
        'name': t,
        'label': labels.get(t, '?'),
        'table_prior': table_prior.get(t, 0),
        'live_prior': x.get('prior_p'),
        'error': x.get('error'),
        'verdict': parse_v(x.get('content')) if not x.get('error') else '失败',
        'conf': parse_conf(x.get('content')),
        'content': x.get('content') or '',
    })

print('===== 控方轮结果明细 =====')
for row in rows:
    print(f"{row['name']:>5s} {row['label']:>4s} 表先验={row['table_prior']:.2f} "
          f"实时先验={row['live_prior'] if row['live_prior'] is not None else float('nan'):.2f} "
          f"控方={row['verdict']:<5s} 置信={row['conf']}")

print()
print('===== 分组统计（控方判伪造） =====')
for grp, desc in (('fake', 'CV漏检伪造20'), ('real', '真实对照20')):
    g = [x for x in rows if x['label'] == grp]
    n_det = sum(1 for x in g if x['verdict'] == '伪造')
    n_det_hi = sum(1 for x in g if x['verdict'] == '伪造' and x['conf'] >= 80)
    n_no = sum(1 for x in g if x['verdict'] == '无伪造')
    n_fail = sum(1 for x in g if x['verdict'] == '失败')
    print(f'  {desc}: 控方判伪造 {n_det} (置信≥80: {n_det_hi}) | 判无伪造 {n_no} | 失败 {n_fail}')
    if grp == 'fake':
        print('    漏掉的伪造:', sorted(x['name'] for x in g if x['verdict'] == '无伪造'))
    else:
        print('    被控方判伪造的真实:', sorted(x['name'] for x in g if x['verdict'] == '伪造'))
