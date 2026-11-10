# -*- coding: utf-8 -*-
"""生成《论文实验设置对比表》——6 篇调研论文 + 本项目基线的横向对比。
数据来源：arXiv 摘要（已核实 ID）+ 领域已知论文报告值；不确定处标注【待核对】。"""
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm

OUT = r"E:\deepfake\研究文档\20261111_论文实验设置对比表.docx"


def set_font(run, size=9, bold=False, ea="宋体", color=None):
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
sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width = Cm(29.7)
sec.page_height = Cm(21.0)
sec.left_margin = sec.right_margin = Cm(1.5)
sec.top_margin = sec.bottom_margin = Cm(1.5)

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("论文实验设置对比表（伪造检测模型架构升级调研）")
set_font(r, 15, True, ea="黑体")
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("2026年11月11日 · 与本项目基线（EfficientNet-B0 / 224×224 / 留出集71.2%）横向对比")
set_font(r, 9, ea="楷体", color=(0x66, 0x66, 0x66))
doc.add_paragraph()

header = ["论文 / 出处", "预处理", "网络与输入", "训练配置", "FF++ c23 成绩",
          "跨库泛化", "可借鉴点", "本项目实测（台账）"]
rows = [
    ["本项目基线\n（对照行）", "insightface 检测 → 人脸1.4倍框+颈部裁剪 → 256 缓存 → 224×224 随机裁剪",
     "EfficientNet-B0 预训练 + 只换输出层；5帧/视频多数投票",
     "AdamW lr=1e-4 + 余弦退火；batch 32；30轮早停；真伪×家族加权采样",
     "—（留出集 71.2%、验证 81.8%）", "—", "—", "留出集 71.2%（2026-11-10 基线）"],
    ["FaceForensics++\nRossler 等 / ICCV 2019\narXiv 1901.08971",
     "人脸检测（Dlib HOG）→ 1.3倍框裁剪 → 缩放 299×299（Xception 输入）",
     "Xception（ImageNet 预训练）全微调",
     "Adam【lr 待核对】；batch 32；约 10 轮",
     "95.73%（二分类，论文报告值）", "—", "评测协议：人脸裁剪预处理 + 逐视频聚合（我们已采用）",
     "✓ 已借鉴人脸裁剪：整帧 50.0% → 裁剪 71.2%（+21.2pp）"],
    ["MesoNet\nAfchar 等 / WIFS 2018\narXiv 1809.00888",
     "人脸检测后直接输入（尺寸较小）",
     "自建浅层网络 Meso-4 / MesoInception-4（参数约 2.8万）",
     "浅层训练、无需预训练权重",
     "未在 FF++ 全面评测（早期数据集上 ~95%）", "—", "轻量化结构参考：参数极少、推理快",
     "待实验"],
    ["F3-Net\nQian 等 / ECCV 2020\narXiv 2007.09355",
     "人脸裁剪（与 FF++ 类似）",
     "Xception 变体 + 频域分解 FAD + 局部频域统计 LFS + MixBlock 融合",
     "【细节待核对】",
     "97.52%（论文报告值）", "优于纯 RGB 方法", "频域幅度谱分支设计——我们阶段3改造首选",
     "待实验（频域分支，优先级 2）"],
    ["SPSL\nLiu 等 / CVPR 2021\n（CVF open access）",
     "人脸裁剪 + 相位谱（DFT 相位）作输入",
     "浅层 CNN（仅 2 个卷积块，参数少）",
     "【细节待核对】",
     "96.91%（论文报告值）", "跨库泛化显著优于深网络（Celeb-DF/DFDC）", "相位谱输入 + 浅层结构：轻量+泛化双对口",
     "待实验（相位谱输入）"],
    ["Face X-ray\nLi 等 / CVPR 2020\narXiv 1912.13458",
     "人脸图 + 自监督生成“X射线”拼接边界灰度图",
     "HRNet 骨干 + 边界线索双通道输入",
     "【细节待核对】",
     "（论文主要报告 AUC 与跨库成绩）", "跨库泛化著称（不依赖具体伪造痕迹）", "输入结构改造：双流输入的直接依据",
     "待实验（双流输入，优先级 1）"],
    ["CBAM\nWoo 等 / ECCV 2018\narXiv 1807.06521",
     "通用模块，无关预处理",
     "通道注意力 + 空间注意力，可插入任意 CNN 中间层",
     "即插即用、开销可忽略",
     "—（ImageNet 提升约 1–2%）", "—", "注意力模块：B0 中段插入即可做 A/B",
     "待实验（注意力模块）"],
    ["DeeperForensics 挑战优胜方案\n（2020）",
     "DF-1.0 官方扰动增强（压缩/模糊/噪声等 7 类×5 档）",
     "EfficientNet-B0/B1/B2 集成",
     "【细节待核对】",
     "挑战赛第一（DF-1.0 基准）", "—", "我们骨干 B0 有先例；扰动增强直接可做",
     "待实验（扰动增强/集成）"],
]
tb = doc.add_table(rows=1 + len(rows), cols=len(header))
tb.style = "Table Grid"
tb.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, htxt in enumerate(header):
    c = tb.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(htxt); set_font(r, 9, True, ea="黑体"); shade(c)
for i, row in enumerate(rows):
    for j, val in enumerate(row):
        c = tb.rows[i + 1].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(val); set_font(r, 8.5, ea="宋体")
widths = [2.7, 3.5, 3.9, 3.1, 2.9, 2.9, 3.4, 3.6]
for j, w in enumerate(widths):
    for row in tb.rows:
        row.cells[j].width = Cm(w)

doc.add_paragraph()
p = doc.add_paragraph()
r = p.add_run("说明：①标注【待核对】的数字来自领域常见报告值，精读原文后修正；"
              "②本项目基线行用于逐项对比“别人怎么设、我们怎么设”；"
              "③改造优先级：双流输入（Face X-ray 依据）→ 频域分支（F3-Net/SPSL）"
              "→ 全解冻/换骨干（FF++ Xception）→ 注意力（CBAM）→ 集成（挑战优胜方案）。")
set_font(r, 9, ea="楷体", color=(0x66, 0x66, 0x66))

doc.save(OUT)
print("已生成:", OUT)
