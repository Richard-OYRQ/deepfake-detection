# -*- coding: utf-8 -*-
"""生成《小模型训练方案》一页纸（A4 单页，发老师用）。"""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm

OUT = r"E:\deepfake\研究文档\20261021_小模型训练方案一页纸.docx"


def set_font(run, size=10.5, bold=False, ea="宋体", color=None):
    run.font.size = Pt(size)
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), ea)
    if color:
        run.font.color.rgb = RGBColor(*color)


def shade(cell, hex_color="D9E2F3"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


doc = Document()
# 窄边距保证一页放下
for sec in doc.sections:
    sec.top_margin = Cm(1.8)
    sec.bottom_margin = Cm(1.8)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)

# 标题
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("深度伪造检测小模型训练方案（一页纸）")
set_font(r, 15, True, ea="黑体")
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("欧阳润谦 · 2026年10月")
set_font(r, 9, ea="楷体", color=(0x66, 0x66, 0x66))
p.paragraph_format.space_after = Pt(6)


def head(text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(6)
    h.paragraph_format.space_after = Pt(2)
    r = h.add_run(text)
    set_font(r, 11, True, ea="黑体", color=(0x1F, 0x3B, 0x63))


def para(text, size=10):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    set_font(r, size, ea="宋体")


def table(header, rows, widths, fs=8.5):
    tb = doc.add_table(rows=1 + len(rows), cols=len(header))
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htxt in enumerate(header):
        c = tb.rows[0].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(htxt); set_font(r, fs, True, ea="黑体"); shade(c)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tb.rows[i + 1].cells[j]; c.text = ""
            r = c.paragraphs[0].add_run(str(val)); set_font(r, fs, ea="宋体")
    for j, w in enumerate(widths):
        for row in tb.rows:
            row.cells[j].width = Cm(w)


# 一、背景与目标
head("一、背景与目标")
para("当前“大模型+规则融合”路线留出复测总正确率 67.5%（160 条，检出 47/80、误报 19/80），"
     "5 折交叉验证 66.5%，已接近规则路线上限，距 85% 目标差距明显。按老师指导，下一阶段转向"
     "自训小模型 + 大数据集路线（学习计划选题三），目标：检测准确率达到 85% 及以上。")

# 二、训练数据
head("二、训练数据")
table(["数据来源", "数量", "用途"],
      [["自建标注基准集（真实+伪造成对）", "200 条", "训练/验证主集"],
       ["自建留出集（80真+80伪）", "160 条", "冻结评估集，不与训练重叠"],
       ["外部评测集（公开换脸家族）", "100 条", "泛化测试"],
       ["开源社区样本（FF++/DFDC/Celeb-DF）", "1100 条", "扩量训练（按家族分层抽样）"],
       ["公开数据集（下载启动中）", "目标 1000+", "训练主体；含美颜/压缩/光照增强"]],
      [6.0, 2.2, 7.4])
p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0)
r = p.add_run("注：美颜/磨皮/压缩为最大混淆源，数据增强必须覆盖，否则训练不充分。")
set_font(r, 8.5, ea="楷体", color=(0x66, 0x66, 0x66))

# 三、模型方案（递进）
head("三、模型方案（递进实施）")
para("方案一（起步）：帧级二分类 CNN——EfficientNet-B0 以 ImageNet 预训练权重微调，输入为人脸裁剪帧"
     "+面颈拼接 ROI 双流；训练快、可解释、易部署。")
para("方案二：时序模型——3D CNN 或帧间差分流，对应提示词中最硬的时序证据（#15 遮挡破坏、#16 转动连续性）。")
para("方案三：LLM 蒸馏——以 qwen3-vl 的 14 项结构化判定为软标签训练专项小模型，继承已调教好的证据概念。")
para("可复用资产：第四信号特征（rPPG/频域/唇同步）已全量提取，可直接作为多模态输入拼接。")

# 四、实施计划
head("四、实施计划与验收")
table(["里程碑", "时间", "目标", "验收标准"],
      [["M1 数据管线", "第1–2周", "数据整合、增强、划分", "标注校验 100% 通过"],
       ["M2 基线模型", "第3–4周", "帧级 CNN 跑通", "留出集正确率 ≥67.5%（追平融合规则）"],
       ["M3 迭代优化", "第5–6周", "时序/多模态特征接入、调参", "较 M2 提升 ≥3 个百分点"],
       ["M4 评估收尾", "第7–8周", "全量测试、报告与 PPT", "混淆矩阵、训练曲线齐备"]],
      [2.6, 2.2, 4.6, 6.2])

# 五、资源与同步
head("五、资源需求与进度同步")
para("资源：GPU（本机或 Colab 免费额度）、公开数据集存储约 100GB。"
     "同步：每周向老师汇报一次进展（数据扩量进度、训练曲线、评估结果），仓库地址 "
     "github.com/Richard-OYRQ/deepfake-detection 供老师随时检查。")

doc.save(OUT)
print("已生成:", OUT)
