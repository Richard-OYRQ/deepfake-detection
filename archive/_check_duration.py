# -*- coding: utf-8 -*-
"""校验：14 个误报真实视频的时长是否系统性偏短（时长特征是第一误报主因的佐证）。"""
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rows = list(csv.DictReader(open(r'D:\deepfake\output\feature_table.csv', encoding='utf-8-sig')))
reals = [r for r in rows if r['label'] == 'real']
fakes = [r for r in rows if r['label'] == 'fake']
misp = ['1', '15', '20', '29', '35', '53', '58', '59', '63', '67', '68', '79', '83', '90']

def d(r):
    return float(r['duration'])

print('真实组时长: 均值 %.1fs  中位 %.1fs  最短 %.1fs  最长 %.1fs' % (
    sum(d(r) for r in reals) / len(reals),
    sorted(d(r) for r in reals)[len(reals) // 2],
    min(d(r) for r in reals), max(d(r) for r in reals)))
print('伪造组时长: 均值 %.1fs  中位 %.1fs' % (
    sum(d(r) for r in fakes) / len(fakes),
    sorted(d(r) for r in fakes)[len(fakes) // 2]))
print()
print('14 个误报真实视频的时长:')
for r in reals:
    stem = r['video'].rsplit('.', 1)[0]
    if stem in misp:
        print('  %s: %.1fs' % (stem, d(r)))
print()
under10 = [r for r in reals if d(r) < 10]
print('真实组中时长<10s的视频: %d 个，其中误报 %d 个' % (
    len(under10),
    sum(1 for r in under10 if r['video'].rsplit('.', 1)[0] in misp)))
