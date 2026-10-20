# -*- coding: utf-8 -*-
"""解析 qwen3-vl-plus 版3对样本的16项评价。"""
import glob
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = sorted(glob.glob(r'D:\deepfake\output_eval3b\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
by = {str(x.get('task_name')): (x.get('content') or '') for x in r['results']}

ITEM_NAMES = {
    '1': '面部边缘模糊/色块/锯齿', '2': '面部拉伸/撕裂/运动脱节',
    '3': '皮肤过度平滑/纹理重复', '4': '肤色与背景冲突/帧间色差',
    '5': '光影方向矛盾/阴影错误', '6': '嘴部语音不同步/唇形僵硬',
    '7': '头发毛边/断层/动态不匹配', '8': '眉毛蜡笔画/睫毛重复/饰品错位',
    '9': '眼球呆滞/反光异常/眨眼异常', '10': '微表情缺失/肌肉僵硬',
    '11': '帧间特征突变/卡顿/闪烁', '12': '头身比异常/颈部色差/脱节',
    '13': '耳朵扭曲/颈部纹理缺失', '14': '背景错位/动态粘连/模糊',
    '15': '遮挡破坏', '16': '转动连续性',
}


def parse_items(content):
    out = {}
    in_table = False
    for line in (content or '').splitlines():
        s = line.strip()
        if s.startswith('| # |') or s.startswith('|---'):
            in_table = True
            continue
        if in_table and s.startswith('|'):
            cols = [c.strip() for c in s.split('|')]
            if len(cols) >= 4 and cols[1].isdigit():
                out[cols[1]] = cols[3].strip().strip('*').strip()
            elif cols and cols[1] and not cols[1].isdigit():
                break
    return out


def parse_verdict(content):
    m = re.search(r'伪造类型判断[：:]\s*\**(.+?)\**\s*(?:\n|$)', content or '')
    return m.group(1).strip() if m else '?'


def parse_conf(content):
    m = re.search(r'综合置信度[：:]\s*\**(\d+)', content or '')
    return m.group(1) if m else '?'


VIDEOS = ['6', 'fake_e6_on_6', '15', 'fake_e15_on_15', '22', 'fake_e22_on_22']
print('===== 模型16项评价（qwen3-vl-plus） =====')
print(f'{"项":>4s} {"项名":<22s} {"6(真)":>8s} {"e6(假)":>8s} {"15(真)":>8s} {"e15(假)":>8s} {"22(真)":>8s} {"e22(假)":>8s}')
for i in range(1, 17):
    k = str(i)
    vals = [parse_items(by.get(v, '')).get(k, '-') for v in VIDEOS]
    print(f'{k:>4s} {ITEM_NAMES[k]:<22s} {vals[0]:>8s} {vals[1]:>8s} {vals[2]:>8s} {vals[3]:>8s} {vals[4]:>8s} {vals[5]:>8s}')

print()
print('===== 综合评估行 =====')
for v in VIDEOS:
    c = by.get(v, '')
    print(f'{v:<16s} 伪造类型={parse_verdict(c):<12s} 置信度={parse_conf(c)}')
