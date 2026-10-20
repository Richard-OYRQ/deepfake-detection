# -*- coding: utf-8 -*-
"""双通道离线模拟（零 API 成本）：
通道A = 无时长 CV 融合先验（特征表）
通道B = 旧激进提示词 VL 判定（8/1 F组文件 + 8/3 真实组文件）
注意：8/1、8/3 的 VL 运行带着旧版定罪式预处理锚定，敏感性/误报都偏高，
生产环境（中性报告）中通道B会明显变弱——此模拟给出的是乐观上界。"""
import csv
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def parse_vl(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


# 通道B：旧激进 VL 判定（F组用8/1文件，真实组用8/3文件）
vl = {}
for path in (r'D:\deepfake\output\results_2026-08-01T17-15-49Z.json',
             r'D:\deepfake\output\results_2026-08-03T17-22-47Z.json'):
    r = json.load(open(path, encoding='utf-8'))
    for x in r['results']:
        t = str(x.get('task_name', ''))
        if x.get('error'):
            vl[t] = '失败'
        else:
            vl[t] = parse_vl(x.get('content'))

# 通道A：无时长融合先验
cv = {}
labels = {}
with open(r'D:\deepfake\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        cv[k] = float(row['prior'])
        labels[k] = row['label']

print('通道B覆盖:', sum(1 for k in labels if k in vl), '/200')
miss_b = [k for k, lb in labels.items() if lb == 'fake' and vl.get(k) == '无伪造']
print('通道B漏检的伪造:', sorted(miss_b), len(miss_b), '个')
fp_b = [k for k, lb in labels.items() if lb == 'real' and vl.get(k) == '伪造']
print('通道B误报的真实:', len(fp_b), '个')
miss_a = [k for k, lb in labels.items() if lb == 'fake' and cv.get(k, 0) < 0.55]
print()
print('通道A(无时长CV)漏检的伪造:', sorted(miss_a), len(miss_a), '个')
inter = set(miss_a) & set(miss_b)
print('两通道同时漏检的伪造:', sorted(inter), len(inter), '个')
print()

# 逻辑1：AND 定罪（两通道一致才硬判伪造）
for thr in (0.50, 0.55, 0.60):
    tp = sum(1 for k, lb in labels.items()
             if lb == 'fake' and cv.get(k, 0) >= thr and vl.get(k) == '伪造')
    fp = sum(1 for k, lb in labels.items()
             if lb == 'real' and cv.get(k, 0) >= thr and vl.get(k) == '伪造')
    print(f'AND定罪 thr={thr}: 检出 {tp} | 误报 {fp} | 综合 {(tp + 100 - fp) / 2:.1f}%')

print()
# 逻辑2：OR 存疑（任一通道阳性 → 存疑；双阳性 → 伪造；双阴 → 无伪造）
for thr in (0.50, 0.55, 0.60):
    fake_verdicts = {'无伪造': 0, '存疑': 0, '伪造': 0}
    real_verdicts = {'无伪造': 0, '存疑': 0, '伪造': 0}
    for k, lb in labels.items():
        a = cv.get(k, 0) >= thr
        b = vl.get(k) == '伪造'
        if a and b:
            v = '伪造'
        elif a or b:
            v = '存疑'
        else:
            v = '无伪造'
        (fake_verdicts if lb == 'fake' else real_verdicts)[v] += 1
    tp = fake_verdicts['伪造']; fn = fake_verdicts['无伪造']
    fp = real_verdicts['伪造']; tn = real_verdicts['无伪造']
    sus = fake_verdicts['存疑'] + real_verdicts['存疑']
    print(f'OR存疑 thr={thr}: 伪造组 {fake_verdicts} | 真实组 {real_verdicts}')
    print(f'   硬检出={tp} 硬漏检={fn} 硬误报={fp} 硬正确={tn} 存疑={sus} '
          f'明确判定正确率={(tp + tn) / 2:.1f}%')
