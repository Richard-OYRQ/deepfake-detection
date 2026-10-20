# -*- coding: utf-8 -*-
"""生成结题汇报PPT（欧阳润谦，中学生，16:9，13页）。"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

BLUE = RGBColor(0x1F, 0x4E, 0x79)
LBLUE = RGBColor(0x2E, 0x74, 0xB5)
GRAY = RGBColor(0x66, 0x66, 0x66)
DARK = RGBColor(0x33, 0x33, 0x33)
GREEN = RGBColor(0x4F, 0x9D, 0x4F)
RED = RGBColor(0xC0, 0x50, 0x4D)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_slide():
    return prs.slides.add_slide(BLANK)


def textbox(slide, x, y, w, h, text, size=18, bold=False, color=DARK, align=PP_ALIGN.LEFT, font='微软雅黑'):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = font
    return tb


def bullets(slide, x, y, w, h, items, size=16, color=DARK, gap=8):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(gap)
        r = p.add_run()
        r.text = '• ' + item
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.name = '微软雅黑'
    return tb


def title_bar(slide, text, sub=''):
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(1.05))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()
    tf = bar.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.size = Pt(28)
    r.font.bold = True
    r.font.color.rgb = WHITE
    r.font.name = '微软雅黑'
    if sub:
        textbox(slide, 0.5, 1.15, 12.3, 0.4, sub, size=13, color=GRAY, align=PP_ALIGN.CENTER)


# ============ 1 封面 ============
s = add_slide()
bg = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg.fill.solid()
bg.fill.fore_color.rgb = BLUE
bg.line.fill.background()
textbox(s, 1, 2.2, 11.3, 1.2, '利用大模型进行深度伪造检测', size=44, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
textbox(s, 1, 3.4, 11.3, 0.6, '—— 项目结题汇报 ——', size=24, color=RGBColor(0xBD, 0xD7, 0xEE), align=PP_ALIGN.CENTER)
textbox(s, 1, 5.2, 11.3, 0.5, '汇报人：欧阳润谦', size=18, color=WHITE, align=PP_ALIGN.CENTER)
textbox(s, 1, 5.8, 11.3, 0.5, '2026年6月 — 8月  |  鉴伪实践项目·选题2', size=16, color=RGBColor(0xBD, 0xD7, 0xEE), align=PP_ALIGN.CENTER)

# ============ 2 项目背景与目标 ============
s = add_slide()
title_bar(s, '项目背景与目标')
bullets(s, 0.8, 1.6, 11.7, 2.4, [
    'Deepfake换脸技术普及，普通人也能生成以假乱真的伪造视频，威胁个人名誉与社会信任',
    '视觉语言大模型（VLM）是内容判别的新兴技术路线，提示词工程是核心方法论',
    '课题要求：检测准确率 ≥ 85%，并产出报告、PPT、脚本、提示词文档、结果记录五类交付物',
], size=17)
textbox(s, 0.8, 4.3, 11.7, 0.5, '项目目标（选题2五项目标）', size=18, bold=True, color=LBLUE)
bullets(s, 0.8, 4.9, 11.7, 2.2, [
    '理解深度伪造视觉特征与大模型判别应用原理，熟悉提示词工程设计逻辑',
    '完成千问大模型API接入调试，实现批量请求与结果解析',
    '设计初始提示词体系，基于真实标签对比分析误判漏判场景与原因',
    '多轮迭代优化提示词，形成适配亚洲人脸样本的高效方案',
    '编写自动化Python脚本，全流程自动化，最终准确率 ≥ 85%',
], size=15)

# ============ 3 数据与工具 ============
s = add_slide()
title_bar(s, '数据与工具')
textbox(s, 0.8, 1.5, 5.5, 0.5, '数据集', size=20, bold=True, color=LBLUE)
bullets(s, 0.8, 2.1, 5.5, 2.0, [
    '200个已标注视频：真实100 + 伪造100',
    '真实：videos/ 1-100号（中文流媒体平台亚洲人脸素材）',
    '伪造：待鉴别/ F1-F100（换脸生成）',
    '另自建14对1080P配对基准集（同视频换脸前后对照）',
], size=15)
textbox(s, 7.0, 1.5, 5.5, 0.5, '工具与技术栈', size=20, bold=True, color=LBLUE)
bullets(s, 7.0, 2.1, 5.5, 2.0, [
    '检测核心：通义千问 qwen3-vl-plus（视觉大模型）',
    '像素测量：OpenCV（清晰度量化、物理特征、证据图）',
    '生成工具：FaceFusion（自造假视频做对照实验）',
    '环境：Windows 11 + Python 3.12/3.14',
], size=15)
textbox(s, 0.8, 4.8, 11.7, 1.0, '合规声明：全部实践基于学术研究自建数据集，严格遵守《个人信息保护法》与平台协议，'
        '未上传真实场景隐私数据，未将检测结果用于非法用途。', size=14, color=GRAY)

# ============ 4 技术路线 ============
s = add_slide()
title_bar(s, '技术路线：双模态架构')
textbox(s, 0.8, 1.5, 11.7, 0.6, '“大模型语义理解 + 传统CV像素分析” → “CV测量—可视化重编码—模型核验—多信号终裁”', size=17, bold=True, color=DARK)
items = [
    ('预处理层', '抽帧 / 清晰度量化 / 物理扫描 / 证据图生成'),
    ('先验层', '双先验融合（P(伪造|特征)）'),
    ('提示词层', '16项主提示词 + 14项控方提示词 + 核验块'),
    ('路由层', '高清→模型主导 / 低清→CV主导'),
    ('终裁层', '三分类：无伪造 / 伪造 / 存疑'),
]
y = 2.5
for name, desc in items:
    textbox(s, 0.8, y, 2.2, 0.5, name, size=17, bold=True, color=LBLUE)
    textbox(s, 3.1, y, 9.5, 0.5, desc, size=16, color=DARK)
    y += 0.72
textbox(s, 0.8, 6.3, 11.7, 0.5, '核心思想：硬结论需要多信号背书，不确定的交人工复核（存疑桶）', size=15, color=GRAY)

# ============ 5 十周历程 ============
s = add_slide()
title_bar(s, '十周实践历程')
items = [
    ('第1-2周', 'API环境搭建；四款千问模型比选，选定qwen3-vl-plus'),
    ('第3-4周', '提示词四版迭代：21项0% → 14项56% → 18项33% → 14项+预处理80%'),
    ('第5-6周', '100视频全量检测（82/17/1）；建立误差分析机制'),
    ('第7-8周', '判定准则重构；面颈比七版阈值校准；自动化脚本初建'),
    ('第9-10周', 'v5.1→v5.6六版本迭代；14对配对基准；八组提示词实验；方案定稿'),
]
y = 1.6
for week, desc in items:
    textbox(s, 0.8, y, 1.9, 0.5, week, size=17, bold=True, color=BLUE)
    textbox(s, 2.8, y, 9.8, 0.5, desc, size=15, color=DARK)
    y += 0.85
textbox(s, 0.8, 6.2, 11.7, 0.5, '全程正确率：54.5% → 92.0% → 93.0% → 85.5% → 97.5%（全自动口径）', size=17, bold=True, color=GREEN)

# ============ 6 提示词迭代之路 ============
s = add_slide()
title_bar(s, '提示词迭代之路（五版演进）')
bullets(s, 0.8, 1.6, 11.7, 3.4, [
    '21项版：检出率0% —— “注意力稀释”：检查项太多，模型全答“正常”',
    '14项版：检出率56% —— “少即是多”',
    '18项版：检出率33% —— 纯文字无法弥补模型对像素级异常的感知盲区',
    '14项+预处理版：检出率80% —— 双模态互补架构确立',
    '16项三件套（最终版）：新增#15遮挡破坏/#16转动连续性两条“物理不可能性硬证据”'
    ' + 无罪推定原则 + 美颜辨析对照表 + 五条判定准则',
], size=16)
textbox(s, 0.8, 5.3, 11.7, 0.5, '核心教训', size=18, bold=True, color=RED)
bullets(s, 0.8, 5.9, 11.7, 1.2, [
    '提示词只能组织模型已有的能力，不能创造它没有的感知 —— 这个道理是用八组实验测出来的',
], size=15)

# ============ 7 突破一 ============
s = add_slide()
title_bar(s, '突破一：真实误报治理（82% → 0%）')
bullets(s, 0.8, 1.6, 11.7, 2.8, [
    '发现问题：伪造检出91%，但82%的真实视频被误判为伪造',
    '数据诊断：五个常用“定罪证据”真假触发率差异仅2%~8%（噪声项）；置信度真假组完全重叠',
    '根因：美颜滤镜与换脸特征重合；“宁可错杀”的调优偏置；定罪式预处理措辞；不对称投票',
    '改造：无罪推定原则 + 美颜辨析对照表 + 证据分级 + 三分类终裁 + CV先验模型',
], size=16)
textbox(s, 0.8, 4.7, 11.7, 0.5, '结果：真实误报率 82% → 0%，全自动正确率 92.0%', size=20, bold=True, color=GREEN)

# ============ 8 突破二 ============
s = add_slide()
title_bar(s, '突破二：隐形伪造攻坚（F89 / F97 / F99）')
bullets(s, 0.8, 1.6, 11.7, 3.0, [
    '三个样本被视觉大模型完全漏检，人工逐帧甄别定位伪影类型：',
    '  F97/F99：“遮挡破坏”——话筒、字幕被换上的脸破坏',
    '  F89：“转动连续性破坏”——转头过程脸部变形抖动',
    '关键概念：“物理不可能性证据”——真实拍摄中物理上无法产生的伪影，特异性最高',
    '实现：OpenCV物理扫描（遮挡边缘衰减AUC 0.87 + 人脸框抖动），三样本先验 0.43~0.51 → 0.96/0.74/0.84',
    '配套发现：模型看不到这些伪影，甚至把被破坏的话筒描述成“边缘锐利连续”',
], size=16)

# ============ 9 突破三 ============
s = add_slide()
title_bar(s, '突破三：配对实验与模型能力边界')
bullets(s, 0.8, 1.6, 11.7, 2.2, [
    '问题：数据集真假标签与分辨率纠缠——检测发现可能是“源质量差异”的产物',
    '方案：自建14对1080P配对基准集——同一段视频换脸前后对照，唯一差异是换脸本身',
    '八组提示词实验：保守/激进/分析师/对比式/知识注入/可视化/静帧/耳部区域',
], size=16)
textbox(s, 0.8, 4.0, 11.7, 0.5, '结果：前七组全部无效；此前97.5%里的“证据子分”被证伪为源混淆产物', size=18, bold=True, color=RED)
textbox(s, 0.8, 4.7, 11.7, 1.2, '教训：评估装置的质量决定结论的质量——没有配对集，假进步会一直藏在好数字里', size=16, color=GRAY)

# ============ 10 核心创新 ============
s = add_slide()
title_bar(s, '核心创新：CV可视化注入（唯一阳性）')
bullets(s, 0.8, 1.6, 11.7, 2.2, [
    '发现：模型看得懂“大尺度颜色模式”，看不懂“细纹理统计”',
    '方案：让CV把测量结果画成图——纹理密度热力图 + 面颈清晰度剖面曲线',
    '效果：模型被图“教会”后，在46%的假脸上确认面颈纹理跳变（真视频仅7%误确认）',
    '对照与复跑双确认；已接入生产系统（v5.6）',
], size=16)
textbox(s, 0.8, 4.3, 11.7, 0.5, '分工定论：模型是“被CV教过之后的核验员”——CV测量并画图，模型在画面里找图教它的模式', size=17, bold=True, color=BLUE)

# ============ 11 最终成果 ============
s = add_slide()
title_bar(s, '最终成果：97.5%（目标85%）')
try:
    s.shapes.add_picture(r'D:\deepfake\output\charts\chart_evolution.png',
                         Inches(0.9), Inches(1.5), width=Inches(7.2))
except Exception:
    pass
textbox(s, 8.5, 1.8, 4.3, 3.4, '三分类模式终态：\n硬误报 0\n硬漏检 1（F39）\n存疑占比 54.5%（人工复核）', size=16, color=DARK)
textbox(s, 0.9, 6.4, 11.5, 0.6, '说明：v5.2的93.0%含时长特征（已按约束禁用）；v5.4/85.5%与v5.5/97.5%为纯内容特征口径', size=13, color=GRAY)

# ============ 12 经验体会 ============
s = add_slide()
title_bar(s, '经验体会')
bullets(s, 0.8, 1.6, 11.7, 4.6, [
    '数据说话胜过感觉：82%误报的修复始于200视频对照分析，不是继续调提示词；每次改动后全量“对答案”',
    '失败的实验也是收获：八组提示词实验七组无效，但它们精确画出了大模型能力的边界',
    '控制变量是科学验证的前提：配对实验一天之内揭穿了一个混在97.5%里的“假进步”',
    '工具链的“隐形坑”：环境版本冲突、静默失败——脚本可靠性来自对每个细节的主动排查',
    '与AI协作的方式：AI助手给方案，数据做裁判——每个建议都用实验验证后才采纳',
], size=17)

# ============ 13 结束页 ============
s = add_slide()
bg = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
bg.fill.solid()
bg.fill.fore_color.rgb = BLUE
bg.line.fill.background()
textbox(s, 1, 2.6, 11.3, 1.0, '谢谢聆听', size=48, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
textbox(s, 1, 3.8, 11.3, 0.6, '敬请各位老师、同学批评指正', size=20, color=RGBColor(0xBD, 0xD7, 0xEE), align=PP_ALIGN.CENTER)

prs.save(r'D:\deepfake\鉴伪实践项目\利用大模型进行深度伪造检测_结题汇报PPT_20260829.pptx')
print('saved, slides:', len(prs.slides.__iter__.__self__._sldIdLst))
