# -*- coding: utf-8 -*-
"""把重建中漏掉的视频（人脸检测随机失败）从备份表合并，新特征列填0。"""
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rows = list(csv.DictReader(open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig')))
back = list(csv.DictReader(open(r'D:\deepfake\output\feature_table_15feat_pure_backup_20260827.csv',
                               encoding='utf-8-sig')))
have = {r['video'] for r in rows}
NEW = ('lip_sync_corr', 'lip_sync_lag')
merged = []
for r in back:
    if r['video'] in have:
        continue
    for k in NEW:
        r[k] = 0
    rows.append(r)
    merged.append(r['video'])
    print('merged:', r['video'], r['label'])
fields = list(rows[0].keys())
with open(r'D:\deepfake\output\feature_table.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
print('total:', len(rows), 'real:', sum(1 for r in rows if r['label'] == 'real'),
      'fake:', sum(1 for r in rows if r['label'] == 'fake'), '| merged:', merged)
