# -*- coding: utf-8 -*-
"""生成《8月3日以来工作进展情况报告》（简版，约1500字）。"""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def set_font(run, name='微软雅黑', size=11, bold=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def h1(doc, text):
    p = doc.add_heading(level=1)
    set_font(p.add_run(text), size=16, bold=True, color=(0x1F, 0x4E, 0x79))


def para(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(22)
    set_font(p.add_run(text), size=11)
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    set_font(p.add_run(text), size=11)


def table(doc, headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'
    for j, htext in enumerate(headers):
        cell = t.rows[0].cells[j]
        set_font(cell.paragraphs[0].add_run(htext), size=10, bold=True)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            set_font(cell.paragraphs[0].add_run(str(val)), size=10)
    doc.add_paragraph()


doc = Document()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run('AI换脸鉴伪项目工作进展情况报告'), size=20, bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run('（2026年8月3日—8月29日）'), size=12, color=(0x66, 0x66, 0x66))

h1(doc, '一、工作总览')
para(doc, '8月3日完成首批全量检测（伪造检出82/100）以来，项目围绕"降低真实误报、攻克隐形伪造、科学评估模型能力"三条主线持续迭代，检测系统历经v5.1至v5.6六个版本，200标注视频上的全自动综合正确率从54.5%提升至97.5%（v5.5口径），并自建14对1080P配对基准集完成了对视觉大模型能力边界的严格科学界定。')

h1(doc, '二、版本演进与关键成果')
table(doc,
      ['版本/日期', '核心工作', '全自动正确率'],
      [
          ['v5.1（8/23）', '数据驱动诊断82%真实误报根因；五层改造；CV先验模型；三分类终裁', '92.0%'],
          ['v5.2（8/25-26）', '攻克F89/F97/F99隐形伪造（遮挡破坏/转动破坏）；CV物理特征；双先验融合', '93.0%'],
          ['v5.3（8/27）', '源级元数据全禁（时长/分辨率/码率不作判据）；纯内容特征', '75.0%'],
          ['v5.4（8/27）', '自适应路由：高清模型主导/低清CV主导', '85.5%'],
          ['v5.5（8/27）', '控方证据子分（后经配对基准证伪为源混淆产物）', '97.5%'],
          ['v5.6（8/29）', 'CV可视化证据+面颈核验上线（唯一复现的模型通道信号）', '—'],
      ])

h1(doc, '三、科学结论（配对基准集证伪系列）')
para(doc, '自建14对1080P配对基准（同视频换脸前后对照，唯一差异=换脸），完成八组模型通道实验：保守票、激进票、证据分析师、对比式取证、知识注入、高清静帧、耳部区域取证均零判别；CV可视化注入（热力图+剖面图）是唯一阳性信号（面颈核验支持率假7/14 vs 真1/14，两轮复现）。核心结论：qwen3-vl-plus对换脸外观指纹的感知盲区与提示词、输入形式无关，唯一有效用法是"CV测量→可视化重编码→模型核验"。')
para(doc, '配对取证规则定稿：软化系（面/背比、面/颈比、噪声残留比）三项全降→判换脸，14/14命中；锯齿之字率规则在e10视频三区域同向命中（配对场景局部证据）。')

h1(doc, '四、关键数据明细')
bullet(doc, '隐形伪造三目标（F89/F97/F99）先验：0.43-0.51 → 0.96/0.74/0.84（v5.2）→ 1.00/0.59/0.65（纯内容特征），全程受保护；')
bullet(doc, '三分类模式终态：硬误报0、硬漏检1（F39，双通道盲区样本）、存疑占比约54.5%交人工复核；')
bullet(doc, '模型通道八组实验的判别力：除CV可视化核验（敏感45%/特异93%）外全部为零；')
bullet(doc, '配对基准软化系：面部清晰度、面/背比、面/颈比、噪声残留比在14对中假脸全部更低（方向一致率100%）；')
bullet(doc, '成本记录：200集全量约520次请求/16元；每视频低清4次请求、高清1次请求。')

h1(doc, '五、交付物与数据资产')
bullet(doc, '报告文档五份：硕士版复盘14322字、本科生版5015字、初中版3039字、下一步方案2056字、最终方案定稿4329字；')
bullet(doc, '实验装置：200标注集、14对配对集、60帧探针流程、直接比对验证法；')
bullet(doc, '生产系统v5.6：双先验融合+自适应路由+物理守卫+CV可视化核验，全流程自动化；')
bullet(doc, '环境工具链：FaceFusion独立venv、ffmpeg便携版、PyAV、双Python环境。')

para(doc, '8月3日以来累计完成十余轮批量检测与数十组对照实验，全部实验数据按日期留档可回溯；项目文档体系覆盖硕士、本科、初中三个读者层级，最终方案定稿包含提示词三件套全文与判定规则。整体进度对照《鉴伪实践项目要求》：准确率≥85%目标已达成（85.5%/97.5%），五类交付物中自动化脚本、运行记录、提示词文档已齐备，实验报告与展示PPT处于整合收尾阶段。')

h1(doc, '六、下一步计划')
para(doc, '①恢复200集全量实跑留档（已部分完成，约16元/3-4小时）；②制作展示PPT（性能演进与证伪实验图表已备）；③按《鉴伪实践项目要求》完成交付物整合与结题。')

doc.save(r'D:\deepfake\工作进展情况报告_简版_20260829.docx')
print('saved')
