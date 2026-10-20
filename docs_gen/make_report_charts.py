# -*- coding: utf-8 -*-
"""生成工作报告配图（PNG）：性能演进、三目标先验跃迁、通道信息量、自适应路由对比。"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = r'D:\deepfake\output\charts'
os.makedirs(OUT, exist_ok=True)

C_BLUE = '#2E74B5'
C_RED = '#C0504D'
C_GREEN = '#4F9D4F'
C_GRAY = '#7F7F7F'
C_ORANGE = '#E07B39'

# ============ 图1：性能演进 ============
fig, ax = plt.subplots(figsize=(7.5, 3.6))
labels = ['旧系统\n(7月)', 'v5.1\n(8/23)', 'v5.2\n(8/26)', 'v5.3\n(8/27)', 'v5.4\n(8/27)']
acc = [54.5, 86.5, 93.0, 75.0, 85.5]
colors = [C_GRAY, C_BLUE, C_BLUE, C_ORANGE, C_GREEN]
bars = ax.bar(labels, acc, color=colors, width=0.55)
for b, v in zip(bars, acc):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f'{v:.1f}%',
            ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_ylim(0, 105)
ax.set_ylabel('全自动综合正确率 (%)')
ax.set_title('各版本全自动综合正确率演进（200 标注视频）', fontsize=12, pad=10)
ax.axhline(90, color=C_RED, linestyle='--', linewidth=1, alpha=0.7)
ax.text(4.42, 91.2, '90% 目标线', color=C_RED, fontsize=9, ha='right')
ax.annotate('源级元数据全禁', xy=(3, 75.0), xytext=(1.2, 62),
            fontsize=9, color=C_ORANGE,
            arrowprops=dict(arrowstyle='->', color=C_ORANGE, lw=1))
ax.annotate('自适应路由', xy=(4, 85.5), xytext=(3.1, 97),
            fontsize=9, color=C_GREEN,
            arrowprops=dict(arrowstyle='->', color=C_GREEN, lw=1))
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'chart_evolution.png'), dpi=160)
plt.close()

# ============ 图2：三目标先验跃迁 ============
fig, ax = plt.subplots(figsize=(7.5, 3.6))
import numpy as np
vids = ['F89', 'F97', 'F99']
old_p = [0.434, 0.433, 0.506]
v52_p = [0.960, 0.738, 0.837]
v53_p = [1.000, 0.588, 0.654]
x = np.arange(3)
w = 0.26
ax.bar(x - w, old_p, w, label='旧模型（8/26前）', color=C_GRAY)
ax.bar(x, v52_p, w, label='v5.2 双先验（含时长）', color=C_BLUE)
ax.bar(x + w, v53_p, w, label='v5.3 纯内容特征', color=C_GREEN)
ax.axhline(0.55, color=C_RED, linestyle='--', linewidth=1)
ax.text(2.35, 0.565, '0.55 定罪线', color=C_RED, fontsize=9, ha='left')
for i in range(3):
    for j, vals in enumerate((old_p, v52_p, v53_p)):
        ax.text(x[i] + (j - 1) * w, vals[i] + 0.02, f'{vals[i]:.2f}',
                ha='center', fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels(vids)
ax.set_ylim(0, 1.15)
ax.set_ylabel('先验 P(伪造)')
ax.set_title('三个隐形伪造样本的先验跃迁', fontsize=12, pad=10)
ax.legend(fontsize=9, loc='upper left')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'chart_prior_jump.png'), dpi=160)
plt.close()

# ============ 图3：通道信息量散点 ============
fig, ax = plt.subplots(figsize=(7.5, 4.0))
points = [
    ('CV先验', 80.2, 79.5, C_BLUE),
    ('CV+物理子分', 83.3, 80.6, C_BLUE),
    ('CV+物理+激进票', 83.3, 78.4, C_ORANGE),
    ('仅激进票', 15.8, 94.3, C_RED),
    ('分析师概率(思考模式)', None, None, C_GRAY),
]
for name, spec, sens, c in points:
    if spec is None:
        ax.text(0.62, 0.32, '证据分析师\n校准概率 AUC=0.53\n≈随机', color=C_GRAY,
                fontsize=10, ha='center',
                bbox=dict(boxstyle='round,pad=0.4', fc='#F2F2F2', ec=C_GRAY))
        continue
    ax.scatter(spec, sens, s=110, color=c, zorder=3, edgecolors='white', linewidths=1.2)
    ax.annotate(name, (spec, sens), textcoords='offset points',
                xytext=(8, -4), fontsize=9)
ax.plot([0, 100], [0, 100], color=C_GRAY, linestyle=':', linewidth=1.2)
ax.text(56, 62, '随机判别线', color=C_GRAY, fontsize=9, rotation=42)
ax.set_xlim(0, 105)
ax.set_ylim(0, 105)
ax.set_xlabel('真实正确率（特异性，%）')
ax.set_ylabel('伪造检出率（敏感性，%）')
ax.set_title('各检测通道的判别力定位（5折交叉验证 / 200视频）', fontsize=12, pad=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'chart_channels.png'), dpi=160)
plt.close()

# ============ 图4：自适应路由对比 ============
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.4), sharey=True)
cats = ['硬检出', '硬漏检', '硬误报']
v53 = [74, 26, 24]
v54 = [74, 26, 3]
x = np.arange(3)
ax1.bar(x - 0.2, v53, 0.4, label='v5.3 纯CV', color=C_ORANGE)
ax1.bar(x + 0.2, v54, 0.4, label='v5.4 自适应路由', color=C_GREEN)
for i in range(3):
    ax1.text(x[i] - 0.2, v53[i] + 1, str(v53[i]), ha='center', fontsize=8)
    ax1.text(x[i] + 0.2, v54[i] + 1, str(v54[i]), ha='center', fontsize=8)
ax1.set_xticks(x)
ax1.set_xticklabels(cats)
ax1.set_ylabel('视频数（共200）')
ax1.set_title('全自动模式：误报 24→3', fontsize=11)
ax1.legend(fontsize=8)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

cats2 = ['存疑占比', '明确无伪造']
v53t = [80.5, 19.5]
v54t = [54.5, 45.5]
ax2.bar(x[:2] - 0.2, v53t, 0.4, label='v5.3', color=C_ORANGE)
ax2.bar(x[:2] + 0.2, v54t, 0.4, label='v5.4', color=C_GREEN)
for i in range(2):
    ax2.text(x[i] - 0.2, v53t[i] + 1, f'{v53t[i]}%', ha='center', fontsize=8)
    ax2.text(x[i] + 0.2, v54t[i] + 1, f'{v54t[i]}%', ha='center', fontsize=8)
ax2.set_xticks(x[:2])
ax2.set_xticklabels(cats2)
ax2.set_ylim(0, 95)
ax2.set_title('三分类模式：存疑 80.5%→54.5%', fontsize=11)
ax2.legend(fontsize=8)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'chart_adaptive.png'), dpi=160)
plt.close()

print('charts saved to', OUT)
