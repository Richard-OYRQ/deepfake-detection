# -*- coding: utf-8 -*-
"""生成近两个月工作进展汇报：文字稿(docx) + PPT(10页)，2026-10-11 导师组汇报。"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pptx import Presentation
from pptx.util import Inches, Pt as PPt
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

DOCX_OUT = r"E:\deepfake\研究文档\20261011_工作进展汇报_文字稿_两月版.docx"
PPTX_OUT = r"E:\deepfake\研究文档\20261011_工作进展汇报_两月版.pptx"

LIVE40 = {"text": "（40条最新策略实测正在进行，预计汇报前出结果）"}

TITLE = "近两个月工作进展汇报（2026年8月11日—10月11日）"
SECTIONS = [
("开场", [
"各位老师好。过去两个月，课题走过了三个阶段：8月的“误报治理期”、9月的“消融审视期”、10月的“验收冲刺期”。两个月的关键词可以各用一个词概括：8月是“止损”——把一场82%误报的事故变成一套证据分级体系；9月是“审判”——把系统里每一条规则都放到实验数据面前过堂；10月是“算账”——把策略演化的得失算成一张清楚的账单。现在课题站在第一阶段验收的最后一个决策点上。",
]),
("一、8月·治理期：一场82%误报的事故和它的遗产", [
"8月23日的一次生产测试中，系统对真实视频的误报率高达82%。排查发现原因很朴素：此前所有提示词调优都在伪造样本上进行，系统被调教成了“宁可错杀”的激进判官。这次事故的遗产是三件现在仍在每天起作用的东西：无罪推定总原则（默认视频真实，只有明确证据链才能翻案）；美颜辨析对照表（把美颜滤镜和换脸蒙版在四个维度上的区别写进提示词——这是亚洲人脸短视频场景最大的干扰源）；软/硬/物理三级证据分级（美颜可解释的现象一律不算伪造证据）。",
"治理效果立竿见影：误报率82%归零，伪造检出保持高位。8月底在自建200条数据集上的官方成绩单是：综合正确率97.5%、硬误报0、存疑率54.5%。",
]),
("二、9月·审视期：把“复杂”放到数据面前", [
"9月的主题是给系统“做体检”。第一项体检是评测集建设：从FaceForensics++等国际公开数据集扩充外部评测集到1100条（真伪各550条），给系统建了一个更大的考场。第二项体检是消融实验：判决层23项参数里5项是死参数、真正起作用的只有1个，把定罪背靠阈值从0.70降到0.55后零误报多捞回21条伪造——系统升级为v5.8。第三项体检是对“分辨率路由”的审判：降清对照实验加变量隔离，证明模型对高清伪造的漏检与分辨率无关，真凶是控方提示词——这套实验链最终导向v5.11的统一流程。",
"这个月还完成了一次重要的方法论证伪：让“辩护人提示词”给存疑样本清账的实验中，它把38条样本翻案37条、真假不分——证明提示词角色当不了仲裁者，仲裁必须依靠硬测量或人工。这个“失败”为课题划掉了一条错误的路线。",
]),
("三、10月·验收期：账单与决策", [
"10月完成了两件事：一是对照豆包大模型的建系方案做了四项改进实验（先验粗筛层、抽帧密度、低清阈值、温度分层），结论是全部否决或降级——参数层的优化空间已被榨干，系统问题上移到了特征分离层面；二是今天上午完成了自建200条数据集的全量离线统计分析——把历史结果存档后，任何新策略都能“重放”到旧数据上，一分钱接口费不花就能算出完整成绩单。",
"统计结果就是今天汇报的核心——一张账单：8月30日的历史版本，伪造检出19条、真实误报1条、综合正确率94.5%；当前的v5.11修正版，伪造检出0条、真实误报0条、综合正确率94.5%。",
"这张账单说明：零误报不是白来的，它的代价是19条检出。背后有一个精确的机理：实验发现8条伪造和1条真实在系统全部可测特征上完全不可分（票型、先验、物理子分、置信度全部重叠）——这“9条不可分样本”就是当前模型能力的边界线。为了零误报，当前版本把定罪权完全交还人工复核。",
"今天下午我们正在用最新提示词工程对自建集真伪各20条抽样做实测验证" + LIVE40["text"] + "。",
]),
("四、关于“85%准确率”的口径与决策点", [
"学习计划要求最终准确率85%以上。我们的系统是三分类（伪造/无伪造/存疑），按综合正确率计算（存疑=移交人工复核，系统未犯错）两个版本都是94.5%，达标；按标准准确率计算（存疑计错）均不达标——这是三分类设计的必然，也是下一步要攻克的真实难点。",
"第一阶段验收面前有两条路：A保守方案——维持零误报配置，检出率0%，定位“筛查机”；B实用方案——自建集专用配置，放开控方定罪限制，恢复约19%检出率、接受约1%误报率。我倾向B：学习计划要求的是“85%准确率并记录误判率”，没有要求零误报；零误报是我们做外部泛化研究时的自我要求，不应锁死第一阶段的实用验收。自建集走B、外部集保持零误报铁律，两条线各按各的目标。",
]),
("五、下一步计划与求助", [
"下一步三件事：第一，PPG心率特征——换脸只替换面部区域，真人面部皮肤有心率引起的周期性微色变，这是当前最有望把检出率拉回来的硬测量特征，计划先在9条不可分样本上做分离性检验；第二，自建集全量200条正式验证，出具第一阶段成绩单；第三，外部评测集1100条上的泛化研究继续推进。",
"想请老师们指导的：一是A/B方案的选择；二是“综合正确率”口径在课题验收中的适用性；三是低成本提升检出率的思路。",
"我的汇报就到这里，谢谢各位老师！",
]),
]

# ======================= docx =======================
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

# ======================= PPT =======================
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
    r.text = "近两个月工作进展汇报"; r.font.size = PPt(48); r.font.bold = True
    r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF); r.font.name = "微软雅黑"
    tb2 = s.shapes.add_textbox(Inches(0.8), Inches(3.5), Inches(11.7), Inches(0.8))
    r2 = tb2.text_frame.paragraphs[0].add_run()
    r2.text = "基于视觉大模型的视频深度伪造检测 · 三阶段：治理 → 审视 → 验收"
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
content("两个月总览：三个阶段，三个关键词", [
    (0, "8月 治理期（止损）：82% 误报事故 → 无罪推定 + 美颜辨析 + 证据分级 → 误报归零"),
    (0, "9月 审视期（审判）：评测集 1100 条 + 消融实验 + 路由审判 → 每一条规则过堂"),
    (0, "10月 验收期（算账）：统一流程 + 豆包方案对比 + 全量离线统计 → 一张账单"),
    (0, "当前：第一阶段验收最后一个决策点（A/B 方案）"),
], size=20)

content("8月·治理期：一场事故的三件遗产", [
    (0, "8/23 事故：真实视频误报率 82%——调优只在伪造样本上做，系统成了激进判官"),
    (0, "遗产① 无罪推定：默认真实，只有明确证据链才能翻案"),
    (0, "遗产② 美颜辨析表：美颜 vs 换脸的四维对照（亚洲短视频最大干扰源）"),
    (0, "遗产③ 证据分级：软/硬/物理三级——美颜可解释的现象不算证据"),
    (0, "8月底成绩单：综合正确率 97.5%、硬误报 0、存疑率 54.5%"),
], size=20)

content("9月·审视期：三场体检", [
    (0, "① 评测集扩容：100 → 1100 条（真伪各 550，FF++ 六方法 + angads24）"),
    (0, "② 消融实验：23 项参数 5 项死参、1 项主导；backstop 0.70→0.55 零误报多捞 21 条 → v5.8"),
    (0, "③ 路由审判：降清对照 + 变量隔离 → 漏检真凶是控方提示词，不是分辨率"),
    (0, "重要证伪：辩护人清账轮 37/38 翻案不分真假——提示词当不了仲裁者"),
    (0, "自建集技术来源确认：faceswapvideo.io（inswapper 系，与 FaceFusion 同源）"),
], size=18)

content("10月·验收期：算账与冲刺", [
    (0, "豆包建系方案对比：fps/粗筛/低清阈值/温度 四项实验 → 全部否决或降级"),
    (0, "今日：自建 200 条全量离线统计（零成本重放方法）+ 40 条最新策略实测"),
    (0, "结论：参数层优化空间已榨干，问题上移到特征分离层面"),
], size=20)

s = prs.slides.add_slide(BLANK)
title_bar(s, "核心发现：一张账单", "零误报不是白来的——它的代价是 19 条检出")
rows = [["策略版本", "伪造检出(共100)", "真实误报(共100)", "综合正确率"],
        ["8月30日 历史版本", "19", "1", "94.5%"],
        ["当前 v5.11 修正版", "0", "0", "94.5%"]]
tbl = s.shapes.add_table(len(rows), 4, Inches(1.6), Inches(1.9), Inches(10.1), Inches(2.6)).table
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j); c.text = v
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = c.text_frame.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER
        if not pr.runs:
            continue
        r = pr.runs[0]; r.font.size = PPt(18 if i else 16); r.font.name = "微软雅黑"
        if i == 0:
            r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF)
        elif i == 2:
            r.font.bold = True; r.font.color.rgb = BLUE
tb2 = s.shapes.add_textbox(Inches(0.8), Inches(5.0), Inches(11.7), Inches(1.8))
tf = tb2.text_frame; tf.word_wrap = True
for k, t in enumerate(["机理：8 条伪造 + 1 条真实在所有可测特征上完全不可分（票型/先验/物理子分/置信度全重叠）",
                       "“9 条不可分样本”= 当前模型能力的精确边界线；为保零误报，定罪权交还人工"]):
    p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
    p.space_after = PPt(6)
    r = p.add_run(); r.text = t
    r.font.size = PPt(16); r.font.name = "微软雅黑"; r.font.color.rgb = GRAY

content("口径与决策点", [
    (0, "85% 口径：综合正确率（存疑不计错）94.5% ✅；标准准确率待新特征突破"),
    (0, "A 保守：检出 0%、误报 0%——“筛查机”定位"),
    (0, "B 实用（我的推荐）：检出约 19%、误报约 1%——符合计划“记录误判率”要求"),
    (0, "思路：自建集走 B 实用验收，外部集保持零误报铁律"),
], size=20)

content("下一步计划与求助", [
    (0, "① PPG 心率特征：换脸破坏面部微色变信号——最有望拉回检出率"),
    (0, "② 自建集全量 200 条正式验证（第一阶段成绩单）"),
    (0, "③ 外部评测集 1100 条泛化研究持续推进"),
    (0, "求助：A/B 方案选择；“综合正确率”口径的适用性；低成本提升检出率思路"),
    (0, "谢谢各位老师！"),
], size=20)

prs.save(PPTX_OUT)
print(f"PPT 已生成（{len(prs.slides._sldIdLst)} 页）: {PPTX_OUT}")
