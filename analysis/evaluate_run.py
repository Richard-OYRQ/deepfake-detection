# -*- coding: utf-8 -*-
"""
运行结果评估：对比真实标注计算混淆矩阵与三分类指标
标注规则：纯数字命名 = 真实；F 命名 = 伪造
用法: python evaluate_run.py <results.json> [--verbose]
"""
import json
import sys

ITEMS = []


def ground_truth(name):
    stem = name.replace('F', 'F')  # 保留原名
    if stem.startswith('F'):
        return 'fake'
    return 'real'


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    verbose = '--verbose' in sys.argv
    if not path:
        print('用法: python evaluate_run.py <results.json> [--verbose]')
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['results']
    # 统计矩阵: gt -> final_verdict
    matrix = {}
    detail = []
    for r in results:
        name = r.get('task_name', '')
        gt = ground_truth(name)
        fv = r.get('final_verdict', '失败' if r.get('error') else '未知')
        matrix.setdefault(gt, {})
        matrix[gt][fv] = matrix[gt].get(fv, 0) + 1
        detail.append((name, gt, fv, r.get('final_confidence', 0), r.get('vote_result')))

    out = []
    def p(line=''):
        out.append(str(line))

    p('=' * 60)
    p(f'  运行评估: {data.get("run_id", path)}')
    p('=' * 60)
    p(f'总视频: {data.get("total")}, 成功: {data.get("succeeded")}, 失败: {data.get("failed")}')
    p()
    p('===== 混淆矩阵 (标注 vs 终裁) =====')
    p(f'{"标注\\终裁":<12s} {"无伪造":>8s} {"伪造":>8s} {"存疑":>8s} {"失败":>8s}')
    for gt in ('real', 'fake'):
        row = matrix.get(gt, {})
        p(f'{gt:<12s} {row.get("无伪造",0):>8d} {row.get("伪造",0):>8d} {row.get("存疑",0):>8d} {row.get("失败",0):>8d}')
    p()

    real = matrix.get('real', {})
    fake = matrix.get('fake', {})
    n_real = sum(real.values())
    n_fake = sum(fake.values())

    tp = fake.get('伪造', 0)
    fn = fake.get('无伪造', 0) + fake.get('存疑', 0) + fake.get('失败', 0)
    tn = real.get('无伪造', 0)
    fp = real.get('伪造', 0) + real.get('存疑', 0) + real.get('失败', 0)

    p('===== 核心指标 =====')
    p(f'伪造检出率 (敏感性): {tp}/{n_fake} = {tp/n_fake*100:.1f}%' if n_fake else '无伪造样本')
    p(f'真实误报率 (1-特异性): {real.get("伪造",0)}/{n_real} = {real.get("伪造",0)/n_real*100:.1f}%' if n_real else '无真实样本')
    p(f'真实正确率 (特异性): {tn}/{n_real} = {tn/n_real*100:.1f}%' if n_real else '')
    p(f'存疑率: 真实 {real.get("存疑",0)}/{n_real}, 伪造 {fake.get("存疑",0)}/{n_fake}')
    p()
    # 硬判准确率（存疑按错误计）
    hard_acc = (tp + tn) / (n_real + n_fake) * 100 if (n_real + n_fake) else 0
    p(f'硬判准确率 (存疑计入错误): {hard_acc:.1f}%')
    p()

    if verbose:
        p('===== 明细 =====')
        for name, gt, fv, conf, vote in sorted(detail):
            p(f'{name:<8s} 标注={gt:<4s} 终裁={fv:<4s} 置信度={conf} 投票={vote}')

    report_path = path.replace('.json', '_evaluation.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f'评估报告: {report_path}')


if __name__ == '__main__':
    main()
