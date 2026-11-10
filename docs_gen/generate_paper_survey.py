# -*- coding: utf-8 -*-
"""生成《伪造检测模型架构升级：论文调研清单》（回应老师"多看论文、改结构"点评）。"""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

OUT = r"E:\deepfake\研究文档\20261110_模型架构升级论文调研清单.docx"


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
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("伪造检测模型架构升级：论文调研清单")
set_font(r, 16, True, ea="黑体")
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("（课题三 · 阶段3 架构改造前期调研 · 2026年11月10日）")
set_font(r, 9.5, ea="楷体", color=(0x66, 0x66, 0x66))
doc.add_paragraph()


def head(text):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(6)
    h.paragraph_format.space_after = Pt(3)
    r = h.add_run(text)
    set_font(r, 12, True, ea="黑体", color=(0x1F, 0x3B, 0x63))


def para(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.first_line_indent = Pt(21)
    r = p.add_run(text)
    set_font(r, 10.5, ea="宋体")


def table(header, rows, widths):
    tb = doc.add_table(rows=1 + len(rows), cols=len(header))
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htxt in enumerate(header):
        c = tb.rows[0].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(htxt); set_font(r, 8.5, True, ea="黑体"); shade(c)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tb.rows[i + 1].cells[j]; c.text = ""
            r = c.paragraphs[0].add_run(str(val)); set_font(r, 8.5, ea="宋体")
    for j, w in enumerate(widths):
        for row in tb.rows:
            row.cells[j].width = Pt(w)


head("一、调研背景")
para("老师点评指出：当前方案（预训练权重 + 只换输出层）上限有限，必须调研现有工作，"
     "学习他人对网络结构、特征层、输入结构的改造思路。本清单按“输入结构、特征层、"
     "网络结构”三个改造轴挑选 6 篇代表性论文，并附实验设置横向对比。"
     "对照基线：本课题人脸裁剪版 EfficientNet-B0，留出集 71.2%、验证集 81.8%。")

head("二、论文选取依据")
para("选取原则：每篇论文必须对应老师点评指出的一个可落地改造方向（网络结构、特征层、"
     "输入结构），且与本课题现状匹配，避免“读了一堆却落不了地”。")
table(["改造轴", "对应论文", "可借鉴的具体动作"],
      [["输入结构", "FaceForensics++ / Face X-ray", "人脸裁剪预处理（已完成）、边界线索双流"],
       ["特征层", "F3-Net（频域幅度谱）/ SPSL（相位谱）/ CBAM", "频域分支、注意力模块"],
       ["网络结构", "MesoNet（轻量浅层）/ Xception 骨干 / 挑战优胜方案（B0 集成）", "换骨干、轻量化、集成"]],
      [80, 220, 210])
para("与项目现状的四点匹配：①骨干同源——本课题用 EfficientNet-B0，特意选入 "
     "DeeperForensics 挑战优胜方案（B0/B1/B2 集成）证明 B0 路线有先例；②定位一致——"
     "“轻量级”是课题硬约束，MesoNet 与 SPSL 均为轻量代表；③痛点对口——本课题刚经历"
     "“真实侧域偏差+背景捷径”，SPSL 与 Face X-ray 以跨数据集泛化强著称，且伪造主体"
     "为换脸拼接，Face X-ray 专门检测拼接边界；④实验可比性——六篇均以 FaceForensics++ "
     "为主要基准，成绩可横向对比，落实老师“横向对比实验设置”的要求。")
para("时间梯度覆盖 2018（MesoNet）→ 2019（FF++）→ 2020（F3-Net/Face X-ray/挑战）→ "
     "2021（SPSL），覆盖伪造检测网络设计从“浅层小网络”到“频域挖掘”再到“泛化导向”"
     "的演进脉络。")
para("说明：本清单基于领域经典论文常识选取，非系统性文献检索结果；论文成绩为报告值"
     "（约值），精读时核对原文。清单不追求全，原则是每篇对应一个下一步可动手的改造；"
     "后续检索到更合适的新方法可替换扩充。")

head("三、论文清单与实验设置对比")
table(["论文", "年份/出处", "核心改造", "骨干/输入", "FF++ c23 报告成绩（约）", "可借鉴点"],
      [["FaceForensics++（Rossler 等）", "ICCV 2019", "伪造检测基准与评测协议", "Xception + 人脸裁剪", "95.7%", "①人脸裁剪预处理与逐帧+聚合评测协议（我们已用）②Xception 骨干替换候选"],
       ["MesoNet（Afchar 等）", "WIFS 2018", "轻量级浅层专用网络（Meso-4/Inception）", "自建小网络", "~95%（早期数据集）", "轻量化结构参考：参数少、推理快，符合“轻量级”定位"],
       ["F3-Net（Qian 等）", "ECCV 2020", "频域线索挖掘：频域分解+局部频域统计双分支", "Xception 变体 + 频域分支", "97.5%", "频域分支设计：DFT 幅度谱作第二输入（伪造伪影常在高频）"],
       ["SPSL（Liu 等）", "CVPR 2021", "相位谱 + 浅层网络，跨库泛化强", "浅层 CNN + 相位谱输入", "96.9%", "相位谱输入 + 浅层结构：参数量小、跨数据集泛化好，直接对口“轻量+泛化”目标"],
       ["Face X-ray（Li 等）", "CVPR 2020", "换脸拼接边界线索：不依赖具体伪造痕迹", "HRNet + 边界线索输入", "（跨库泛化著称）", "输入结构改造：人脸图+边界线索双通道，正对口我们“全局+局部双流”规划"],
       ["DeeperForensics 挑战优胜方案", "2020", "EfficientNet-B0/B1/B2 集成 + 扰动增强", "EfficientNet 系", "挑战赛第一", "我们的骨干正是 B0：集成与扰动增强直接可做；验证“B0 路线有先例可循”"]],
      [105, 55, 110, 90, 75, 120])

head("四、改造路线图（阶段3 执行计划）")
table(["改造轴", "具体动作", "对应论文", "预期收益", "验证方式"],
      [["输入结构", "①人脸+面颈裁剪（已完成）②加“局部放大流”做双流输入③加边界线索通道", "FaceForensics++ / Face X-ray", "消除背景捷径、增强边界伪影敏感度", "同考卷 A/B 对比"],
       ["特征层", "①在 B0 中段插入 CBAM 注意力②加频域分支（DFT 幅度谱/相位谱第二输入）", "CBAM(ECCV2018) / F3-Net / SPSL", "聚焦伪造敏感区域与高频伪影", "同考卷 A/B 对比"],
       ["网络结构", "①全解冻微调（vs 只训分类头）②骨干换 Xception 或加 MesoNet 浅层并行③B0/B1 集成", "Xception / MesoNet / 挑战优胜方案", "提升上限、增强泛化", "同考卷 A/B 对比"]],
      [70, 190, 110, 100, 80])
para("执行纪律：每次只改一个变量，用同一套考卷（160 留出 + 174 第二卷）评分，"
     "与 71.2% 基线逐项对比；每项改造记录“改动、动机、成绩变化、结论”四要素，"
     "形成阶段3 消融报告。")

head("五、下一步安排")
para("①本周：完成清单内论文精读 3 篇（F3-Net、SPSL、Face X-ray），输出实验设置对比表；"
     "②下周起逐项落地改造（先做实现成本最低的双流输入与全解冻对比）；"
     "③同步推进数据补充（自建真实素材采集）与 StyleGAN/扩散样本调研。")

doc.save(OUT)
print("已生成:", OUT)
