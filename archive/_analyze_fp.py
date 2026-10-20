# -*- coding: utf-8 -*-
"""
对照分析：用两批已标注数据评估 14 项检测指标的判别力
- 真实组: output/results_2026-08-03T17-22-47Z.json (videos/ 1-100, 全部真实)
- 伪造组: output/results_2026-08-01T17-15-49Z.json (待鉴别/ F1-F100, 全部伪造)
"""
import json
import re
from collections import Counter

ITEMS = [
    (1, '面部边缘模糊/色块/锯齿'),
    (2, '面部拉伸/撕裂/运动脱节'),
    (3, '皮肤过度平滑/纹理重复'),
    (4, '肤色与背景冲突/帧间色差'),
    (5, '光影方向矛盾/阴影错误'),
    (6, '嘴部语音不同步/唇形僵硬'),
    (7, '头发毛边/断层/动态不匹配'),
    (8, '眉毛蜡笔画/睫毛重复/饰品错位'),
    (9, '眼球呆滞/反光异常/眨眼异常'),
    (10, '微表情缺失/肌肉僵硬'),
    (11, '帧间特征突变/卡顿/闪烁'),
    (12, '头身比异常/颈部色差/脱节'),
    (13, '耳朵扭曲/颈部纹理缺失'),
    (14, '背景错位/动态粘连/模糊'),
]


def parse_one(content):
    """从单条检测内容中提取: 逐项判定, 伪造类型, 置信度"""
    if not content:
        return None
    item_verdicts = {}
    for num, name in ITEMS:
        # 匹配表格行: | 1 | 名称 | 判定 | 时间戳 | 说明 |
        m = re.search(
            r'\|\s*%d\s*\|\s*[^|]*?\|\s*\*{0,2}(正常|可疑|异常)\*{0,2}\s*\|' % num,
            content)
        if m:
            item_verdicts[num] = m.group(1)
    m2 = re.search(r'伪造类型判断[：:]\s*\*{0,2}(.+?)\*{0,2}\s*[\r\n]', content)
    fake_type = m2.group(1).strip() if m2 else 'unknown'
    m3 = re.search(r'综合置信度[：:]\s*\*{0,2}(\d+)\s*/\s*100', content)
    confidence = int(m3.group(1)) if m3 else -1
    m4 = re.search(r'异常项统计[：:]\s*\*{0,2}(\d+)\s*/\s*14', content)
    anomaly_count = int(m4.group(1)) if m4 else -1
    return {'items': item_verdicts, 'type': fake_type, 'conf': confidence, 'anom': anomaly_count}


def load(path, ground_truth):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    rows = []
    for r in data['results']:
        if r.get('error'):
            continue
        p = parse_one(r.get('content', ''))
        if not p:
            continue
        verdict = p['type']
        is_fake_verdict = '无伪造' not in verdict
        if ground_truth == 'fake':
            correct = is_fake_verdict
        else:
            correct = not is_fake_verdict
        rows.append({
            'name': r['task_name'], 'verdict': verdict, 'conf': p['conf'],
            'anom': p['anom'], 'correct': correct, 'items': p['items'],
        })
    return rows


real_set = load(r'D:\deepfake\output\results_2026-08-03T17-22-47Z.json', 'real')
fake_set = load(r'D:\deepfake\output\results_2026-08-01T17-15-49Z.json', 'fake')

out = []
def p(line=''):
    out.append(str(line))

n_real = len(real_set)
n_fake = len(fake_set)
fp_real = sum(1 for r in real_set if not r['correct'])
tn_real = n_real - fp_real
tp_fake = sum(1 for r in fake_set if r['correct'])
fn_fake = n_fake - tp_fake

p(f'===== 总体表现 =====')
p(f'真实组 (n={n_real}): 误报 {fp_real} ({fp_real*100//n_real}%), 正确 {tn_real}')
p(f'伪造组 (n={n_fake}): 检出 {tp_fake} ({tp_fake*100//n_fake}%), 漏检 {fn_fake}')
p()
p(f'===== 逐项判别力分析 =====')
p(f'{"#":>3s} {"检测项":<26s} {"真实组可疑率":>10s} {"伪造组可疑率":>10s} {"差异":>6s} {"判别力":>6s}')
p('-' * 78)

item_rate_real = {}
item_rate_fake = {}
for num, name in ITEMS:
    def rate(rows):
        total = 0
        susp = 0
        for r in rows:
            v = r['items'].get(num)
            if v is None:
                continue
            total += 1
            if v in ('可疑', '异常'):
                susp += 1
        return susp / total if total else 0
    rr = rate(real_set)
    rf = rate(fake_set)
    diff = rf - rr
    if diff >= 0.25:
        power = '★★★强'
    elif diff >= 0.12:
        power = '★★中'
    elif diff >= 0.0:
        power = '★弱'
    else:
        power = '✗ 噪声'
    p(f'{num:>3d} {name:<26s} {rr*100:>9.1f}% {rf*100:>9.1f}% {diff*100:>+5.1f}% {power:>6s}')
    item_rate_real[num] = rr
    item_rate_fake[num] = rf

p()
p(f'===== 误报真实视频的证据模式 (被判伪造的 {fp_real} 个) =====')
anom_fp = Counter()
for r in real_set:
    if not r['correct']:
        for num, v in r['items'].items():
            if v in ('可疑', '异常'):
                anom_fp[num] += 1
for num, cnt in anom_fp.most_common():
    name = dict((n, m) for n, m in ITEMS)[num]
    p(f'  #{num} {name}: {cnt}/{fp_real} ({cnt*100//fp_real}%)')

p()
p(f'===== 漏检伪造视频的"正常"项 (被判无伪造的 {fn_fake} 个) =====')
normal_fn = Counter()
for r in fake_set:
    if not r['correct']:
        for num, v in r['items'].items():
            if v == '正常':
                normal_fn[num] += 1
for num, cnt in normal_fn.most_common():
    name = dict((n, m) for n, m in ITEMS)[num]
    p(f'  #{num} {name}: {cnt}/{fn_fake} 判为正常')

p()
p(f'===== 置信度分布 =====')
p(f'真实组误报的置信度: {sorted(r["conf"] for r in real_set if not r["correct"])}')
p(f'真实组正确的置信度: {sorted(r["conf"] for r in real_set if r["correct"])}')
p(f'伪造组检出的置信度: {sorted(r["conf"] for r in fake_set if r["correct"])}')
p(f'伪造组漏检的置信度: {sorted(r["conf"] for r in fake_set if not r["correct"])}')
p()
p(f'===== 异常项计数分布 =====')
p(f'真实组(误报): {sorted(Counter(r["anom"] for r in real_set if not r["correct"]).items())}')
p(f'真实组(正确): {sorted(Counter(r["anom"] for r in real_set if r["correct"]).items())}')
p(f'伪造组(检出): {sorted(Counter(r["anom"] for r in fake_set if r["correct"]).items())}')
p(f'伪造组(漏检): {sorted(Counter(r["anom"] for r in fake_set if not r["correct"]).items())}')

with open(r'D:\deepfake\_fp_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
