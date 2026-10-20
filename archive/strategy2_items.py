# -*- coding: utf-8 -*-
"""策略二：配对集"看见层"逐项证据重新检验。
用已有14对控方轮逐项数据，在源质量受控的配对集上检验每个单项的残余方向。"""
import glob
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
ITEM_NAMES = {
    '1': '面部边缘模糊/色块/锯齿', '2': '面部拉伸/撕裂/运动脱节',
    '3': '皮肤过度平滑/纹理重复', '4': '肤色与背景冲突/帧间色差',
    '5': '光影方向矛盾/阴影错误', '6': '嘴部语音不同步/唇形僵硬',
    '7': '头发毛边/断层/动态不匹配', '8': '眉毛蜡笔画/睫毛重复/饰品错位',
    '9': '眼球呆滞/反光异常/眨眼异常', '10': '微表情缺失/肌肉僵硬',
    '11': '帧间特征突变/卡顿/闪烁', '12': '头身比异常/颈部色差/脱节',
    '13': '耳朵扭曲/颈部纹理缺失', '14': '背景错位/动态粘连/模糊',
}

files = sorted(glob.glob(BASE + r'\output_benchpros\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
by = {str(x.get('task_name')): (x.get('content') or '') for x in r['results']}


def parse_items(content):
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
                out[cols[1]] = cols[3]
            elif cols and cols[1] and not cols[1].isdigit():
                break
    return out


print('===== 配对集"看见层"逐项检验（14对，控方14项） =====')
print(f'{"项":>4s} {"项名":<24s} {"假·异常":>8s} {"真·异常":>8s} {"假·异常+可疑":>10s} {"真·异常+可疑":>10s} {"成对差(异常)":>10s}')
survivors = []
for i in range(1, 15):
    k = str(i)
    fa = ra = fs = rs = 0
    pair_diff = 0
    for n in NUMS:
        fv = parse_items(by.get('fake_e%d_on_%d' % (n, n), ''))
        rv = parse_items(by.get('%d' % n, ''))
        f = fv.get(k, '')
        rr = rv.get(k, '')
        if f == '异常':
            fa += 1
        if rr == '异常':
            ra += 1
        if f in ('异常', '可疑'):
            fs += 1
        if rr in ('异常', '可疑'):
            rs += 1
        if f == '异常' and rr != '异常':
            pair_diff += 1
        elif f != '异常' and rr == '异常':
            pair_diff -= 1
    mark = ''
    if fa > ra:
        survivors.append((k, ITEM_NAMES[k], fa, ra))
        mark = ' <-- 残余正向'
    print(f'{k:>4s} {ITEM_NAMES[k]:<24s} {fa:>8d} {ra:>8d} {fs:>10d} {rs:>10d} {pair_diff:>+10d}{mark}')

print()
print('===== 结论 =====')
if survivors:
    print('假脸异常率高于真视频的单项（"看见层"残余信号候选）:')
    for k, name, fa, ra in survivors:
        print(f'  #{k} {name}: {fa}/14 vs {ra}/14')
else:
    print('无任何单项在配对集上表现出残余正向——"看见层"在源质量受控后完全蒸发')
