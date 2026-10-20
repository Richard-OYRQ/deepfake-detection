# -*- coding: utf-8 -*-
"""把 96.mp4 / F88.mp4（人脸检测随机失败）从旧表合并进新特征表，新特征填0。"""
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rows = list(csv.DictReader(open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig')))
back = list(csv.DictReader(open(r'D:\deepfake\output\feature_table_16feat_dur_backup_20260826.csv',
                               encoding='utf-8-sig')))
have = {r['video'] for r in rows}
NEW = ('noise_ratio', 'chroma_diff', 'rot_diff_energy', 'flow_consistency')
for r in back:
    if r['video'] in have:
        continue
    for k in NEW:
        r[k] = 0
    rows.append(r)
    print('merged:', r['video'], r['label'])
fields = list(rows[0].keys())
with open(r'D:\deepfake\output\feature_table.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
print('total:', len(rows), 'real:', sum(1 for r in rows if r['label'] == 'real'),
      'fake:', sum(1 for r in rows if r['label'] == 'fake'))
