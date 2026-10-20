# -*- coding: utf-8 -*-
"""生成《外部评测集1000视频分类清单与流派目录》Word 文档（两部分）。"""
import collections
import json
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

rows = json.load(open(r"E:\DeepFake\外部评测集100\bench_rows.json", encoding="utf-8"))
# rows: [name, kind, method, res, source]

METHODS = ["DeepFakeDetection", "Deepfakes", "Face2Face", "FaceShifter", "FaceSwap", "NeuralTextures", "未标注(FF++衍生)"]
METHOD_CN = {
    "DeepFakeDetection": "DeepFakeDetection（深度伪造检测网络）",
    "Deepfakes": "DeepFakes（自编码器换脸）",
    "Face2Face": "Face2Face（面部表情重演）",
    "FaceShifter": "FaceShifter（高保真换脸）",
    "FaceSwap": "FaceSwap（图形学换脸）",
    "NeuralTextures": "NeuralTextures（神经纹理重演）",
    "未标注(FF++衍生)": "未标注（FF++衍生批次）",
}


def tier(res):
    try:
        w, h = map(int, res.split("x"))
        return "高清(≥1280×720)" if (w >= 1280 and h >= 720) else "低清(<1280×720)"
    except Exception:
        return "未知"


doc = Document()
for sec in doc.sections:
    sec.top_margin = Cm(2.0); sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.0); sec.right_margin = Cm(2.0)


def set_font(run, name="宋体", size=12, bold=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), name)


def title(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run(text), name="黑体", size=16, bold=True)
    p.paragraph_format.space_after = Pt(6)


def h1(text):
    p = doc.add_paragraph()
    set_font(p.add_run(text), name="黑体", size=14, bold=True, color=(0x1F, 0x4E, 0x79))
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)


def h2(text):
    p = doc.add_paragraph()
    set_font(p.add_run(text), name="黑体", size=11.5, bold=True, color=(0x2E, 0x74, 0xB5))
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)


def para(text, size=10.5, bold=False):
    p = doc.add_paragraph()
    set_font(p.add_run(text), size=size, bold=bold)
    p.paragraph_format.space_after = Pt(3)
    return p


def table(headers, data, font_size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, htxt in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        set_font(c.paragraphs[0].add_run(htxt), name="黑体", size=font_size, bold=True)
    for row in data:
        cells = t.add_row().cells
        for i, ctxt in enumerate(row):
            cells[i].text = ""
            set_font(cells[i].paragraphs[0].add_run(str(ctxt)), size=font_size)
    doc.add_paragraph()
    return t


def li(no, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.7)
    p.paragraph_format.first_line_indent = Cm(-0.7)
    p.paragraph_format.line_spacing = 1.15
    set_font(p.add_run(no), size=9)
    set_font(p.add_run(text), size=9)
    return p


title("外部评测集 1000 视频分类清单与流派目录")
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(sub.add_run("数据位置：E:\\DeepFake\\外部评测集100（real 500 / fake 500）｜生成日期：2026-09-13"), size=9, color=(0x80, 0x80, 0x80))
doc.add_paragraph()

# ================= 第一部分 =================
h1("第一部分：1000 视频分类列表")

h2("1.1 总体构成")
fake_by_method = collections.Counter(r[2] for r in rows if r[1] == "fake")
real_count = sum(1 for r in rows if r[1] == "real")
table(["类别", "数量", "说明"], [
    ["真实视频", real_count, "angads24 批次 200 + FF++ c23 批次 300"],
    *[["伪造视频", v, METHOD_CN.get(k, k)] for k, v in sorted(fake_by_method.items())],
    ["合计", len(rows), "1000 个，无损坏文件"],
])

h2("1.2 真伪 × 分辨率档 交叉统计")
c = collections.Counter((r[1], tier(r[3])) for r in rows)
table(["真伪", "高清(≥1280×720)", "低清(<1280×720)", "小计"], [
    ["真实", sum(v for (k, t), v in c.items() if k == "real" and t.startswith("高清")),
     sum(v for (k, t), v in c.items() if k == "real" and t.startswith("低清")), real_count],
    ["伪造", sum(v for (k, t), v in c.items() if k == "fake" and t.startswith("高清")),
     sum(v for (k, t), v in c.items() if k == "fake" and t.startswith("低清")),
     len(rows) - real_count],
])

h2("1.3 伪造流派 × 分辨率档 交叉统计")
tdata = []
for m in METHODS:
    ms = [r for r in rows if r[2] == m]
    if not ms:
        continue
    hi = sum(1 for r in ms if tier(r[3]).startswith("高清"))
    lo = len(ms) - hi
    tdata.append([METHOD_CN.get(m, m).split("（")[0], hi, lo, len(ms)])
table(["伪造流派", "高清(≥1280×720)", "低清(<1280×720)", "小计"], tdata)

h2("1.4 完整分类列表（1000 条）")
para("排序规则：真伪（真实在前）→ 流派（字母序）→ 分辨率 → 文件名。", size=9)
order = {"real": 0, "fake": 1}
sorted_rows = sorted(rows, key=lambda r: (order[r[1]], r[2] if r[1] == "fake" else "真实", r[3], r[0]))
big = [["#", "文件名", "真伪", "伪造流派", "分辨率", "分辨率档", "来源"]]
for i, (name, kind, method, res, src) in enumerate(sorted_rows, 1):
    big.append([i, name, "真实" if kind == "real" else "伪造",
                method if kind == "fake" else "—", res, tier(res), src])
t = table(big[0], big[1:], font_size=8)
para("注：分辨率档按项目路由标准划分（宽≥1280 且高≥720 为高清）。", size=9)

# ================= 第二部分 =================
h1("第二部分：伪造技术流派目录清单")
para("以下按伪造技术流派分组列出全部 500 个伪造视频（文件名 + 分辨率），供按流派取用与实验对照。", size=10)

for m in METHODS:
    ms = sorted([r for r in rows if r[2] == m], key=lambda r: r[0])
    if not ms:
        continue
    res_dist = ", ".join(f"{k}×{v}" for k, v in
                         sorted(collections.Counter(r[3] for r in ms).items(), key=lambda x: -x[1]))
    h2(f"2.{METHODS.index(m) + 1} {METHOD_CN.get(m, m)}（共 {len(ms)} 个）")
    para(f"分辨率分布：{res_dist}", size=9)
    for i, r in enumerate(ms, 1):
        li(f"{i}.", f"{r[0]} —— {r[3]}")

doc.save(r"E:\DeepFake\外部评测集1000分类清单与流派目录.docx")
print("DOCX saved")
