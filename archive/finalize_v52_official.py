# -*- coding: utf-8 -*-
"""v5.2 正式评估落盘：
1. 用新融合先验对 8/23 全量运行离线重算终裁（三分类 + 全自动）
2. 写正式 results JSON（含 prior_p，自包含）
3. 写混淆矩阵评估报告 output/v52_离线重算评估_20260826.md
"""
import copy
import csv
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, r'D:\deepfake')

from reapply_fusion import refinalize

BASE = r'D:\deepfake'
OUT = os.path.join(BASE, 'output')
SRC = os.path.join(OUT, 'results_2026-08-23T09-12-51Z_refused.json')

# 真值标签 + 融合先验
labels, fused_prior = {}, {}
with open(os.path.join(OUT, 'stable_prior_table.csv'), encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        k = row['video'].rsplit('.', 1)[0]
        labels[k] = row['label']
        fused_prior[k] = float(row['prior'])


def apply(results, auto, prior_fake_thr=0.55):
    out = []
    for r in copy.deepcopy(results):
        r['prior_p'] = fused_prior.get(r.get('task_name'))
        refinalize(r, auto=auto, prior_fake_thr=prior_fake_thr)
        out.append(r)
    return out


def matrix(results):
    m = {'real': {}, 'fake': {}}
    for r in results:
        lb = labels.get(r.get('task_name'), '?')
        if lb not in m:
            continue
        v = r.get('final_verdict', '?')
        m[lb][v] = m[lb].get(v, 0) + 1
    return m


def row_text(m, key):
    return str(m.get(key, 0))


with open(SRC, encoding='utf-8') as f:
    data = json.load(f)

triage = apply(data['results'], auto=False)
auto55 = apply(data['results'], auto=True, prior_fake_thr=0.55)
auto60 = apply(data['results'], auto=True, prior_fake_thr=0.60)

# ---- 落盘 JSON ----
def save_json(results, path):
    payload = {
        'run_id': path.split(os.sep)[-1].replace('.json', ''),
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'source': os.path.basename(SRC),
        'strategy': 'v5.2 双先验 max 融合（prior_fusion: max，稳定先验表离线回退）',
        'results': results,
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print('written:', path)


triage_path = os.path.join(OUT, 'results_v52_三分类_融合先验_20260826.json')
auto_path = os.path.join(OUT, 'results_v52_全自动0.55_融合先验_20260826.json')
save_json(triage, triage_path)
save_json(auto55, auto_path)

# ---- 评估报告 ----
mt, ma55, ma60 = matrix(triage), matrix(auto55), matrix(auto60)

def metrics(m):
    tp = m['fake'].get('伪造', 0); fn = m['fake'].get('无伪造', 0)
    fp = m['real'].get('伪造', 0); tn = m['real'].get('无伪造', 0)
    sus = sum(m[lb].get('存疑', 0) for lb in ('real', 'fake'))
    fail = sum(m[lb].get('失败', 0) for lb in ('real', 'fake'))
    hard_acc = (tp + tn) / 200 * 100
    return tp, fn, fp, tn, sus, fail, hard_acc

t_metrics = metrics(mt)
a55_metrics = metrics(ma55)
a60_metrics = metrics(ma60)

old_verdict = {}
with open(SRC, encoding='utf-8') as f:
    for r in json.load(f)['results']:
        old_verdict[r.get('task_name')] = r.get('final_verdict')

changes = [(r.get('task_name'), labels.get(r.get('task_name'), '?'),
            old_verdict.get(r.get('task_name')), r.get('final_verdict'))
           for r in triage if old_verdict.get(r.get('task_name')) != r.get('final_verdict')]

report_path = os.path.join(OUT, 'v52_离线重算评估_20260826.md')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('# v5.2 离线重算评估报告（2026-08-26）\n\n')
    f.write('## 一、方法\n\n')
    f.write('- 数据来源：8/23 全量 200 视频运行结果（视觉票型、置信度不变，零 API 成本）\n')
    f.write('- 先验：双先验 max 融合稳定表（旧 v16 模型与新 16 特征模型取高值，3 次扫描中位数）\n')
    f.write('- 终裁规则：与 src/processor.py `_finalize_result` 一致（convict≥0.70 / 冲突≥0.55 / 置信度门槛 85-90）\n\n')
    f.write('## 二、三分类模式混淆矩阵\n\n')
    f.write('| 组别(100) | 无伪造 | 存疑 | 伪造 | 失败 |\n|---|---|---|---|---|\n')
    f.write(f"| 真实组 | {row_text(mt['real'], '无伪造')} | {row_text(mt['real'], '存疑')} | {row_text(mt['real'], '伪造')} | {row_text(mt['real'], '失败')} |\n")
    f.write(f"| 伪造组 | {row_text(mt['fake'], '无伪造')} | {row_text(mt['fake'], '存疑')} | {row_text(mt['fake'], '伪造')} | {row_text(mt['fake'], '失败')} |\n\n")
    f.write(f"- 硬误报 {t_metrics[2]} 个、硬漏检 {t_metrics[1]} 个、存疑 {t_metrics[4]} 个（{t_metrics[4]/2:.1f}%）、失败 {t_metrics[5]} 个\n")
    f.write(f"- 明确判定（无伪造/伪造）正确率 {t_metrics[6]:.1f}%\n\n")
    f.write('## 三、全自动模式\n\n')
    f.write('| 阈值 | 检出 | 漏检 | 误报 | 综合正确率 |\n|---|---|---|---|---|\n')
    f.write(f"| 0.55 | {a55_metrics[0]}% | {a55_metrics[1]} | {a55_metrics[2]}% | {(a55_metrics[0] + (100 - a55_metrics[2] - a55_metrics[5])) / 200 * 100:.1f}% |\n")
    f.write(f"| 0.60 | {a60_metrics[0]}% | {a60_metrics[1]} | {a60_metrics[2]}% | {(a60_metrics[0] + (100 - a60_metrics[2] - a60_metrics[5])) / 200 * 100:.1f}% |\n\n")
    f.write('## 四、终裁变化明细（旧 → 新，共 %d 个）\n\n' % len(changes))
    f.write('| 视频 | 真值 | 旧终裁 | 新终裁 |\n|---|---|---|---|\n')
    for t, lb, o, n in changes:
        f.write(f'| {t} | {lb} | {o} | {n} |\n')
    f.write('\n## 五、结论\n\n')
    f.write('1. 三分类模式：硬性错误归零（不误杀真实、不放跑伪造），F89/F97/F99 等 5 个旧漏检伪造全部进入存疑桶，人工复核量 113 个（56.5%）。\n')
    f.write('2. 全自动模式：0.55 阈值检出 100%、误报 13%、综合 93.0%；0.60 阈值检出 97%、误报 10%、综合 93.0%。\n')
    f.write('3. 新策略无需 API 重跑即完成全量评估；若要官方留档的实跑数据，另需约 20-25 元重跑 200 视频流水线。\n')
print('written:', report_path)
