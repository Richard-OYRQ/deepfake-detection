# -*- coding: utf-8 -*-
"""确认实验汇总分析：E(有图) vs E0(无图严格对照) vs E2(有图复跑) + 联合规则。"""
import glob
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]


def load(d):
    files = sorted(glob.glob(BASE + r'\%s\results*.json' % d))
    if not files:
        return {}
    r = json.load(open(files[-1], encoding='utf-8'))
    return {str(x.get('task_name')): (x.get('content') or '') for x in r['results']}


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


E = load('output_E')
E0 = load('output_E0')
E2 = load('output_E2')

print('数据: E=%d视频 E0=%d视频 E2=%d视频' % (len(E), len(E0), len(E2)))


def group_stats(by, key='3'):
    """核验3的 支持/反对/无法 分组统计。返回 (假支持,假反对,假无法,真支持,真反对,真无法)。"""
    from collections import Counter
    fc, rc = Counter(), Counter()
    for n in NUMS:
        for tag, grp in (('%d' % n, 'real'), ('fake_e%d_on_%d' % (n, n), 'fake')):
            v = parse_verdicts(by.get(tag, '')).get(key, '?')
            (fc if grp == 'fake' else rc)[v] += 1
    return (fc.get('支持', 0), fc.get('反对', 0), fc.get('无法判定', 0),
            rc.get('支持', 0), rc.get('反对', 0), rc.get('无法判定', 0))


print()
print('===== 核验③（视频画面核验）三组对比 =====')
for tag, by in (('E  有图·首轮', E), ('E0 无图·对照', E0), ('E2 有图·复跑', E2)):
    fs, fo, fu, rs, ro, ru = group_stats(by)
    print(f'{tag:<12s} 假脸: 支持{fs:>2} 反对{fo:>2} 无法{fu:>2} | 真视频: 支持{rs:>2} 反对{ro:>2} 无法{ru:>2}')

print()
print('===== 联合规则（E轮：核验③支持 AND 面颈比<0.8 → 伪造） =====')
# 面颈比（用锚值文件重建）
ratios = {}
import re
for n in NUMS:
    for tag, path in (('%d' % n, BASE + r'\videos\%d.mp4' % n),
                      ('fake_e%d_on_%d' % (n, n),
                       BASE + r'\pairset\outputs\fake_e%d_on_%d.mp4' % (n, n))):
        with open(BASE + r'\_pairE\%s.txt' % tag, encoding='utf-8') as f:
            txt = f.read()
        m = re.search(r'面颈清晰度比=([\d.]+)', txt)
        ratios[tag] = float(m.group(1)) if m else -1
tp = fp = fn = tn = 0
for n in NUMS:
    fk = 'fake_e%d_on_%d' % (n, n)
    rk = '%d' % n
    fv = parse_verdicts(E.get(fk, '')).get('3', '?') == '支持'
    rv = parse_verdicts(E.get(rk, '')).get('3', '?') == '支持'
    fr = ratios.get(fk, -1) < 0.8
    rr = ratios.get(rk, -1) < 0.8
    if fv and fr:
        tp += 1
    elif not fv and fr:
        fn += 1
    if rv and rr:
        fp += 1
    elif not rv and rr:
        tn += 1
print(f'敏感性 {tp}/14  特异性 {tn}/{tn+fp}  假脸漏检 {fn}  真视频误伤 {fp}')
