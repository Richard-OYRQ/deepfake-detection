# -*- coding: utf-8 -*-
"""生成近一个月工作进展汇报：8分钟文字稿(docx) + PPT(9页)，2026-10-11 导师组汇报。"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pptx import Presentation
from pptx.util import Inches, Pt as PPt
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

DOCX_OUT = r"E:\deepfake\研究文档\20261011_工作进展汇报_文字稿.docx"
PPTX_OUT = r"E:\deepfake\研究文档\20261011_工作进展汇报.pptx"

# 40条实测结果占位（跑完后更新）
LIVE40 = {"done": False, "text": "（40条实测正在进行，预计汇报前出结果）"}

# ======================= 文字稿 =======================
TITLE = "近一个月工作进展汇报（2026年9月11日—10月11日）"
SECTIONS = [
("开场", [
"各位老师好。过去一个月，课题完成了从“系统优化”到“工程验收”的转向：数据集、提示词体系、自动化检测脚本都已就绪，当前的核心工作是第一阶段验收的最后一公里——并且我们发现了一个必须用数据来决策的真实取舍。",
]),
("一、这个月完成的三件事", [
"第一，系统完成了一轮“瘦身与加固”。9月27日，我们用消融实验给判决层做体检：23项可调参数中5项是死参数，真正起作用的只有1个定罪背靠阈值，把它从0.70降到0.55后，在零误报前提下多抓回21条伪造，系统升级为v5.8。随后我们又用实验链审判了“分辨率路由”：降清对照实验和变量隔离证明，模型对高清伪造的漏检与分辨率无关，真正的根源是控方提示词，于是系统升级为v5.11——废除路由、统一流程、结构性保证零误报。回顾这一个月的版本演进，每一步都遵循同一条纪律：任何规则改动都必须通过同批视频的配对验证，不允许凭感觉动配置。",
"第二，方法论上的两次重要证伪。我们试过让“辩护人提示词”为存疑样本清账：它把38条存疑样本翻案了37条、真假不分，证明提示词角色当不了仲裁者，仲裁必须依靠硬测量或人工。我们还对照豆包大模型的建系方案做了四项改进实验——先验粗筛层、抽帧密度、低清置信度门槛、温度分层——结论是全部否决或降级：参数层的优化空间已经被榨干，系统的问题上移到了特征分离层面。这两次证伪看似“白做”，但它们为课题省下了继续在错误方向上投入的整块时间。",
"第三，今天上午完成了自建200条数据集的全量离线统计分析。方法说明一下：把历史检测结果完整存档后，判决层的任何新策略都可以“重放”到旧数据上——一分钱接口费不花，几十秒算完一个版本的完整成绩单。这是本课题的“零成本评审”方法。同时确认了自建伪造集的技术来源：通过faceswapvideo.io网站生成，属于inswapper系消费级换脸（与主流换脸工具FaceFusion同源）——这意味着我们的自建集覆盖的是“普通人最容易接触到的伪造方式”，有真实的威胁场景价值。",
]),
("二、核心发现：一张账单", [
"把8月30日的历史版本和当前版本放在同一批200条自建数据上对比：",
"历史版本：伪造检出19条、真实误报1条、综合正确率94.5%；当前版本：伪造检出0条、真实误报0条、综合正确率94.5%。",
"这张账单说明一件事：零误报不是白来的，它的代价是19条检出。过去一个月我们把系统改得更安全了，但更安全不等于更好用——这是一个真实的工程取舍，今天的汇报主要就是想把它摆在老师们面前。",
"账单单背后的机理也值得讲清楚：当前版本之所以检出为0，是因为“控方轮永不定罪”条款——控方提示词对伪造的敏感度高达91%，但它对真实视频同样多疑，我们在实验中发现有8条伪造和1条真实在全部可测特征上完全不可分（票型、先验分数、物理特征子分、置信度全部重叠），为了保证零误报，只能把它们全部交给人工复核。这就是“9条不可分样本”的故事——它精确标注了当前系统的能力边界。",
"今天下午我们正在用最新提示词工程对自建集真伪各20条的抽样做实测验证，" + LIVE40["text"] + "。",
]),
("三、关于“85%准确率”的口径说明", [
"学习计划要求最终准确率85%以上。我们的系统是三分类输出（伪造/无伪造/存疑），需要明确口径：按综合正确率计算（存疑=移交人工复核，系统在存疑上没有犯错），两个版本都是94.5%，达标；按标准准确率计算（存疑按错误计），都不达标。这是三分类设计下的必然结果，也是我们下一步要攻克的真实难点——计划的标准口径85%需要新特征才能突破。",
]),
("四、一个决策点，请老师们给意见", [
"第一阶段验收面前有两条路：A方案（保守）：维持当前的零误报配置，检出率0%，所有可疑样本进存疑池交人工复核，定位是“筛查机”；B方案（实用）：自建集专用配置，放开控方定罪限制，恢复约19%的检出率，接受约1%的误报率。",
"我倾向B方案，理由是：学习计划要求的是“85%准确率并记录误判率”，没有要求零误报——零误报是我们做外部泛化研究时给自己定的更高标准，不应该反过来锁死第一阶段的实用验收。自建集用B（有检出、有可报告的误判率），外部集继续保持零误报铁律，两条线各按各的目标走。",
]),
("五、下一步计划与求助", [
"下一步三件事：第一，PPG心率特征——换脸只替换面部区域，真人面部皮肤存在心率引起的周期性微色变，这是当前最有希望把检出率拉回来的硬测量特征，计划在9条“不可分样本”上先做分离性检验；第二，自建集全量200条的正式验证，出具第一阶段成绩单；第三，外部评测集（1100条）上的泛化研究继续推进。",
"想请老师们指导的：一是A/B方案的选择；二是“综合正确率”这个口径在课题验收中的适用性；三是如果有更好的零成本或低成本检出率提升思路，希望得到指点。",
"我的汇报就到这里，谢谢各位老师！",
]),
]

# ======================= 生成 docx =======================
doc = Document()
for sec in doc.sections:
    sec.top_margin = Cm(2.5); sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.8); sec.right_margin = Cm(2.8)

def set_font(run, name="宋体", size=12, bold=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts"); rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), name)

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run(TITLE), name="黑体", size=16, bold=True)
total = len(TITLE)
for head, paras in SECTIONS:
    p = doc.add_paragraph()
    set_font(p.add_run(head), name="黑体", size=13, bold=True, color=(0x1F, 0x4E, 0x79))
    total += len(head)
    for text in paras:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Pt(24)
        p.paragraph_format.line_spacing = 1.4
        set_font(p.add_run(text))
        total += len(text)
doc.save(DOCX_OUT)
print(f"文字稿已生成（约 {total} 字）: {DOCX_OUT}")

# ======================= 生成 PPT =======================
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLUE = PRGB(0x1F, 0x4E, 0x79)
LBLUE = PRGB(0x2E, 0x74, 0xB5)
GRAY = PRGB(0x40, 0x40, 0x40)
BLANK = prs.slide_layouts[6]

def add_rect(slide, x, y, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh

def title_bar(slide, text, sub=None):
    add_rect(slide, 0, 0, prs.slide_width, Inches(1.0), BLUE)
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.12), Inches(12.3), Inches(0.8))
    r = tb.text_frame.paragraphs[0].add_run(); r.text = text
    r.font.size = PPt(28); r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF)
    r.font.name = "微软雅黑"
    if sub:
        sb = slide.shapes.add_textbox(Inches(0.55), Inches(0.62), Inches(12), Inches(0.35))
        r2 = sb.text_frame.paragraphs[0].add_run(); r2.text = sub
        r2.font.size = PPt(12); r2.font.color.rgb = PRGB(0xD0, 0xE0, 0xF0); r2.font.name = "微软雅黑"

def bullets(slide, items, x=0.6, y=1.3, w=12.1, h=5.9, size=18):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, (level, text) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = level
        p.space_after = PPt(10)
        r = p.add_run(); r.text = ("• " if level == 0 else "– ") + text
        r.font.size = PPt(size if level == 0 else size - 3)
        r.font.name = "微软雅黑"
        r.font.color.rgb = GRAY if level == 0 else LBLUE
        if text.startswith("【"):
            r.font.bold = True; r.font.color.rgb = BLUE

def cover():
    s = prs.slides.add_slide(BLANK)
    add_rect(s, 0, 0, prs.slide_width, prs.slide_height, BLUE)
    add_rect(s, 0, Inches(4.9), prs.slide_width, Inches(0.06), PRGB(0xFF, 0xC0, 0x00))
    tb = s.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.7), Inches(1.6))
    r = tb.text_frame.paragraphs[0].add_run()
    r.text = "近一个月工作进展汇报"; r.font.size = PPt(48); r.font.bold = True
    r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF); r.font.name = "微软雅黑"
    tb2 = s.shapes.add_textbox(Inches(0.8), Inches(3.5), Inches(11.7), Inches(0.8))
    r2 = tb2.text_frame.paragraphs[0].add_run()
    r2.text = "基于视觉大模型的视频深度伪造（DeepFake）检测 · 第一阶段验收冲刺"
    r2.font.size = PPt(22); r2.font.color.rgb = PRGB(0xD0, 0xE0, 0xF0); r2.font.name = "微软雅黑"
    tb3 = s.shapes.add_textbox(Inches(0.8), Inches(5.2), Inches(11.7), Inches(0.8))
    r3 = tb3.text_frame.paragraphs[0].add_run()
    r3.text = "汇报人：________    2026年10月11日"
    r3.font.size = PPt(16); r3.font.color.rgb = PRGB(0xE8, 0xE8, 0xE8); r3.font.name = "微软雅黑"

def content(title, items, sub=None, size=18):
    s = prs.slides.add_slide(BLANK)
    title_bar(s, title, sub)
    bullets(s, items, size=size)
    return s

cover()
content("一个月总览：从系统优化到工程验收", [
    (0, "数据 ✅：自建200条成对数据集（inswapper系换脸，标注明确）"),
    (0, "系统 ✅：提示词三件套定稿 + 判决层瘦身加固（v5.8 → v5.11）"),
    (0, "实验 ✅：四轮实验链 + 豆包方案对比，参数层优化空间已榨干"),
    (0, "当前：第一阶段验收最后一公里——一个需要用数据决策的取舍"),
], size=20)

s = prs.slides.add_slide(BLANK)
title_bar(s, "一个月的系统演进（时间线）", "每一版都有实验数据背书")
timeline = [
    "9/27 v5.8：消融体检——删5个死参数、backstop 0.70→0.55（+21条检出、零误报）",
    "9/28-30 路由审判：降清实验+变量隔离 → 真凶是控方提示词，不是分辨率",
    "10/8 v5.11：统一流程 + 结构性零误报（控方轮永不定罪）",
    "10/9-10 豆包方案对比：fps/粗筛/阈值/温度 四项实验全部否决或降级",
    "10/11 今日：自建200条全量离线统计 + 40条最新策略实测",
]
tb = s.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(11.7), Inches(5.6))
tf = tb.text_frame; tf.word_wrap = True
for i, t in enumerate(timeline):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = PPt(14)
    r = p.add_run(); r.text = "→ " + t
    r.font.size = PPt(18); r.font.name = "微软雅黑"
    r.font.color.rgb = BLUE if i == len(timeline) - 1 else GRAY

s = prs.slides.add_slide(BLANK)
title_bar(s, "今日成果：自建200条全量离线统计", "零成本重放方法：历史结果存档 → 新策略重放 → 完整成绩单")
rows = [["策略版本", "伪造检出(共100)", "真实误报(共100)", "综合正确率"],
        ["8月30日 历史版本", "19", "1", "94.5%"],
        ["当前 v5.11 修正版", "0", "0", "94.5%"],
        ["当前+冲突0.45", "0", "0", "96.0%"]]
tbl = s.shapes.add_table(len(rows), 4, Inches(1.6), Inches(2.2), Inches(10.1), Inches(3.2)).table
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j); c.text = v
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = c.text_frame.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER
        r = pr.runs[0]; r.font.size = PPt(18 if i else 16); r.font.name = "微软雅黑"
        if i == 0:
            r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF)
        elif i == 2:
            r.font.bold = True; r.font.color.rgb = BLUE
tb2 = s.shapes.add_textbox(Inches(0.8), Inches(5.8), Inches(11.7), Inches(1.2))
r = tb2.text_frame.paragraphs[0].add_run()
r.text = "【账单】零误报不是白来的——它的代价是 19 条检出。" + LIVE40["text"]
r.font.size = PPt(16); r.font.bold = True; r.font.color.rgb = PRGB(0xC0, 0x00, 0x00)
r.font.name = "微软雅黑"

content("口径说明：85% 怎么算", [
    (0, "我们的系统是三分类：伪造 / 无伪造 / 存疑（移交人工复核）"),
    (0, "综合正确率（存疑不计错）：94.5% ✅ 达标 85%"),
    (0, "标准准确率（存疑计错）：不达标——三分类设计的必然结果"),
    (0, "下一步攻克标准口径需要新特征（PPG 心率信号）"),
], size=20)

s = prs.slides.add_slide(BLANK)
title_bar(s, "决策点：第一阶段验收走哪条路", "请老师们给意见")
rows = [["", "A 保守方案", "B 实用方案（我的推荐）"],
        ["检出率", "0%", "约 19%"],
        ["误报率", "0%", "约 1%（计划允许记录误判率）"],
        ["定位", "筛查机（全交人工）", "有检出的检测系统"],
        ["依据", "零误报铁律（外部泛化研究标准）", "学习计划：85%准确率+记录误判率"]]
tbl = s.shapes.add_table(len(rows), 3, Inches(1.3), Inches(1.6), Inches(10.7), Inches(3.6)).table
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j); c.text = v
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = c.text_frame.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER
        if not pr.runs:
            continue
        r = pr.runs[0]; r.font.size = PPt(16 if i else 15); r.font.name = "微软雅黑"
        if i == 0 or j == 0:
            r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF) if i == 0 else BLUE
        if j == 2:
            r.font.bold = True
tb2 = s.shapes.add_textbox(Inches(0.8), Inches(5.6), Inches(11.7), Inches(1.2))
r = tb2.text_frame.paragraphs[0].add_run()
r.text = "思路：自建集走 B（实用验收），外部集保持零误报铁律——两条线各按各的目标。"
r.font.size = PPt(16); r.font.name = "微软雅黑"; r.font.color.rgb = GRAY

content("下一步计划", [
    (0, "① PPG 心率特征：换脸破坏面部皮肤微色变信号——当前最有望拉回检出率"),
    (1, "在 9 条不可分样本上先做分离性检验（1-2 天开发）"),
    (0, "② 自建集全量 200 条正式验证（第一阶段成绩单）"),
    (0, "③ 外部评测集（1100 条）泛化研究继续推进"),
], size=20)

content("请老师们指导", [
    (0, "A/B 方案的选择：保守 0 检出 vs 实用 19% 检出 + 1% 误报"),
    (0, "“综合正确率”口径在课题验收中的适用性"),
    (0, "低成本提升检出率的思路指点"),
    (0, "谢谢各位老师！"),
], size=20)

prs.save(PPTX_OUT)
print(f"PPT 已生成（{len(prs.slides._sldIdLst)} 页）: {PPTX_OUT}")
