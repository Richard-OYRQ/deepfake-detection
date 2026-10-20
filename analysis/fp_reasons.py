# -*- coding: utf-8 -*-
"""误报清单与误判理由：三分类硬误报 + 全自动误报24个，逐视频给出触发信号与理由。"""
import csv
import glob
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\deepfake')

from reapply_fusion import refinalize
import copy

BASE = r'D:\deepfake'
files = sorted(glob.glob(BASE + r'\output_full200\results*.json'))
r = json.load(open(files[-1], encoding='utf-8'))
results = r['results']

labels = {}
with open(BASE + r'\output\stable_prior_table.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        labels[row['video'].rsplit('.', 1)[0]] = row['label']


def parse_verdict(content):
    for line in (content or '').splitlines():
        if '伪造类型判断' in line:
            return '伪造' if any(k in line for k in ('换脸', '面部重演', '全生成')) else \
                   ('无伪造' if '无伪造' in line else '?')
    return '?'


def parse_conf(content):
    m = re.search(r'置信度[：:]\s*\**(\d+)', content or '')
    return int(m.group(1)) if m else 0


def parse_cv_verify(content):
    m = re.search(r'面颈纹理跳变核验[：:]\s*\**\s*(支持|反对|无法判定)', content or '')
    return m.group(1) if m else '无'


# 三分类硬误报
print('========== A. 三分类硬误报（真实被判伪造） ==========')
for x in results:
    t = str(x.get('task_name')).rsplit('.', 1)[0]
    if labels.get(t) == 'real' and x.get('final_verdict') == '伪造':
        c = x.get('content') or ''
        v = parse_verdict(c)
        conf = parse_conf(c)
        ev = x.get('evidence_score', '无')
        cv = parse_cv_verify(c)
        # 定罪路径判断
        if v == '伪造' and conf >= 85:
            path = '初筛保守票直接定罪（伪造票+置信≥85）'
        else:
            path = '双背书定罪（伪造票+先验≥0.70）'
        print(f'视频: {t}')
        print(f'  先验: {x.get("prior_p")} | 证据子分: {ev} | 核验: {cv}')
        print(f'  误判理由: {path}；模型判定"{v}"、置信{conf}')
        # 模型自述理由（关键证据行）
        for line in c.splitlines():
            s = line.strip()
            if s.startswith(('1.', '2.', '3.')) and '证据' not in s:
                print(f'  模型自述: {s[:70]}')
        print()

# 全自动误报
print('========== B. 全自动模式误报（先验≥0.55判伪造的真实视频，24个） ==========')
auto = copy.deepcopy(results)
for x in auto:
    refinalize(x, auto=True, prior_fake_thr=0.55, prior_real_thr=0.45)
rows = []
for x in auto:
    t = str(x.get('task_name')).rsplit('.', 1)[0]
    if labels.get(t) == 'real' and x.get('final_verdict') == '伪造':
        rows.append((t, x.get('prior_p', 0), x.get('evidence_score', 0),
                     parse_cv_verify(x.get('content', ''))))
rows.sort(key=lambda r: -r[1])
print(f'{"视频":>5s} {"先验":>7s} {"证据子分":>8s} {"核验":>6s} {"触发信号"}')
for t, p, ev, cv in rows:
    triggers = []
    if p >= 0.55:
        triggers.append('先验≥0.55')
    if ev >= 3:
        triggers.append('证据子分≥3')
    print(f'{t:>5s} {p:>7.3f} {str(ev):>8s} {cv:>6s} {"+".join(triggers)}')
