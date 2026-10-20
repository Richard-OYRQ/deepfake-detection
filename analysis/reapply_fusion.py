# -*- coding: utf-8 -*-
"""
离线重算终裁：把 v3 融合规则应用到已有 run 的 results JSON（零 API 成本）
规则（与 src/processor.py _finalize_result 一致）：
  1. 失败 → 失败
  2. 票型分裂 → 存疑
  3. 任一伪造票 + 先验≥0.70 → 伪造
  4. 无伪造 + 先验≥0.55（冲突）→ 存疑
  5. 无伪造 置信≥90 → 无伪造；伪造类 置信≥85 → 伪造；否则存疑
用法: python reapply_fusion.py <results.json>
"""
import csv
import json
import os
import re
import sys

import numpy as np

# 先验回退（当 results 中无 prior_p 字段时使用，例如早期的全量运行）：
# 优先用稳定先验表（与生产运行的 stable_prior_probability 一致），
# 不存在时回退到特征表+先验模型计算
_BASE = os.path.dirname(os.path.abspath(__file__))
_feature_prior = {}
try:
    stable_path = os.path.join(_BASE, 'output', 'stable_prior_table.csv')
    if os.path.exists(stable_path):
        with open(stable_path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                _feature_prior[row['video'].rsplit('.', 1)[0]] = float(row['prior'])
    else:
        with open(os.path.join(_BASE, 'src', 'prior_model.json'), encoding='utf-8') as f:
            _model = json.load(f)
        with open(os.path.join(_BASE, 'output', 'feature_table.csv'), encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                z = _model.get('bias', 0.0)
                for name, mu, sd, w in zip(_model['features'], _model['mu'], _model['sd'], _model['weights']):
                    x = float(row.get(name, 0) or 0)
                    sd = sd if sd > 1e-9 else 1.0
                    z += w * (x - mu) / sd
                p = 1.0 / (1.0 + np.exp(-max(-30.0, min(30.0, z))))
                _feature_prior[row['video'].rsplit('.', 1)[0]] = float(p)
except Exception:
    _feature_prior = {}


def parse_verdict(content):
    if not content:
        return 'unknown'
    for line in content.split('\n'):
        if '伪造类型判断' in line:
            if '无伪造' in line:
                return '无伪造'
            if '面部重演' in line:
                return '面部重演'
            if '换脸' in line:
                return '换脸'
            if '全生成' in line:
                return '全生成'
    return 'unknown'


def parse_conf(content):
    if not content:
        return 0
    m = re.search(r'置信度[：:]\s*\*{0,2}(\d+)\s*/\s*100', content)
    return int(m.group(1)) if m else 0


def refinalize(r, conflict_thr=0.55, convict_prior=0.70,
               real_conf=90, fake_conf=85, auto=False,
               prior_fake_thr=0.60, prior_real_thr=0.45,
               prior_convict_backstop=0.55):
    if r.get('error') is not None:
        r['final_verdict'] = '失败'
        r['final_confidence'] = 0
        return r
    verdict = parse_verdict(r.get('content', ''))
    conf = parse_conf(r.get('content', ''))
    tally = r.get('vote_result')
    prior = r.get('prior_p')
    if prior is None:
        prior = _feature_prior.get(r.get('task_name', ''))
    # ---- 全自动模式：先验主判 + 边界带模型票 ----
    if auto and prior is not None:
        if prior >= prior_fake_thr:
            r['final_verdict'] = '伪造'
        elif prior < prior_real_thr:
            r['final_verdict'] = '无伪造'
        elif tally is not None:
            fake_votes = sum(tally.get(k, 0) for k in ('换脸', '面部重演', '全生成'))
            r['final_verdict'] = '伪造' if fake_votes >= 1 else '无伪造'
        else:
            r['final_verdict'] = '无伪造'
        r['final_confidence'] = conf
        return r
    # ---- 三分类模式 ----
    if tally is not None:
        fake_votes = sum(tally.get(k, 0) for k in ('换脸', '面部重演', '全生成'))
        if fake_votes >= 1 and prior is not None and prior >= convict_prior:
            r['final_verdict'] = '伪造'
            r['final_confidence'] = conf
            return r
    if tally and len(tally) > 1:
        r['final_verdict'] = '存疑'
    elif tally is not None:
        if verdict == '无伪造':
            if prior is not None and prior >= conflict_thr:
                r['final_verdict'] = '存疑'
            else:
                r['final_verdict'] = '无伪造' if conf >= real_conf else '存疑'
        elif verdict in ('换脸', '面部重演', '全生成'):
            # v5.7：伪造票定罪需先验背书
            r['final_verdict'] = '伪造' if (conf >= fake_conf and prior is not None
                                            and prior >= prior_convict_backstop) else '存疑'
        else:
            r['final_verdict'] = '存疑'
    else:
        # 单票结果
        if verdict == '无伪造':
            if prior is not None and prior >= conflict_thr:
                r['final_verdict'] = '存疑'
            else:
                r['final_verdict'] = '无伪造' if conf >= real_conf else '存疑'
        elif verdict in ('换脸', '面部重演', '全生成'):
            # v5.7：伪造票定罪需先验背书
            r['final_verdict'] = '伪造' if (conf >= fake_conf and prior is not None
                                            and prior >= prior_convict_backstop) else '存疑'
        else:
            r['final_verdict'] = '存疑'
    r['final_confidence'] = conf
    return r


def main():
    path = sys.argv[1]
    auto = '--auto' in sys.argv
    suffix = '_auto.json' if auto else '_refused.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for r in data['results']:
        refinalize(r, auto=auto)
    out_path = path.replace('.json', suffix)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('written:', out_path)


if __name__ == '__main__':
    main()
