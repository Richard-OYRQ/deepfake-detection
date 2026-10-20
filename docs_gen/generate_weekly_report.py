# -*- coding: utf-8 -*-
"""生成近三周工作汇报：3000字文字稿(docx) + PPT(pptx)，2026-09-27 导师组汇报用。"""
import re
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pptx import Presentation
from pptx.util import Inches, Pt as PPt
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

DOCX_OUT = r"E:\deepfake\研究文档\20260927_近三周工作汇报_文字稿_v2.docx"
PPTX_OUT = r"E:\deepfake\研究文档\20260927_近三周工作汇报_v2.pptx"

# ======================= 文字稿正文 =======================
TITLE = "近三周工作汇报（2026年9月6日—9月27日）"
SECTIONS = [
("开场与总览", [
"各位老师好，下面我汇报最近三周我在“基于视觉大模型的视频深度伪造（DeepFake）检测”课题上的工作。",
"先简单介绍一下我们的检测系统。它由两个部分组成：视觉大模型负责逐帧观看视频，检查十几项面部线索（边缘、光影、唇形、微表情等）并投票；计算机视觉程序负责测量面部清晰度等量化指标，给出一个“先验分数”，表示可疑程度。两部分就像法庭里的陪审团和物证鉴定，最后由判决层综合它们给出结论：伪造、无伪造，或者存疑——拿不准就交给人工复核。这项研究的意义在于：AI换脸技术越来越逼真，网络上的虚假视频可能被用来骗人，如果我们能让检测系统又准又快，就能帮大家少上当。",
"这三周的工作围绕一个问题展开：我们已经有了一套能用的检测系统，但它是不是太复杂了？判决层的二十个规则里，哪些真正起作用、哪些是多余的？围绕这个问题，我完成了三件事：第一，把测试用的评测集从200条扩充到1100条，给系统建了一个更大的“考场”；第二，对系统的判决层做了一次系统的消融实验——就是每次只关掉一个规则、看结果怎么变的对照实验；第三，根据实验结果把系统简化升级为v5.8，并正在做最终验证。",
]),
("一、评测集建设：给系统一个公平的“考场”", [
"要客观评价检测系统好不好，必须有带标准答案的测试视频集，就像考试要有答案才能判分。9月13日，我从公开的FaceForensics++等国际数据集下载了带官方真伪标签的视频，建成外部评测集：第一批100条，逐步扩充到1000条；9月27日又补充了100条。现在评测集共1100条，真实和伪造各550条，伪造部分覆盖了六种主流伪造方法（换脸、面部重演、神经纹理等）。题目种类越多，考出来的成绩越可信——因为不同伪造手段留下的痕迹各不相同。",
"需要特别说明的是，这些真伪标签只用于考后判分：检测的时候，系统完全不知道文件名和来源，防止“看着答案做题”。这个原则还来自我们的一个教训：模型曾经靠视频时长、分辨率这些“场外信息”猜答案，后来把元数据全部屏蔽，正确率立刻从93%掉到75%——说明之前有一部分成绩是“作弊”得来的。",
"有了这个考场，系统的每一次改动都可以量化打分。打分用三个指标：检出率——真伪造里被正确抓出的比例；误报率——真视频被冤枉成伪造的比例；存疑率——系统拿不准、交给人工复核的比例。",
]),
("二、文档沉淀与基线实验", [
"9月13日，我把前期提示词调优的完整过程整理成两份研究文档：《提示词工程调优过程回顾》和《鉴伪策略与决策流程及局限性分析》。整理过程中，我对系统的理解加深了一层：回顾五个阶段的提示词演化，确认了“做减法”的重要性——第一阶段设计者写了21项检测指标，结果检出率是0%；删到14项后反而升到56%。这说明规则不是越多越好，每条规则都会分散模型的注意力。后来在14项基础上只加回了2项“物理不可能”证据：遮挡物边缘断裂、转头时五官跳动——这两种现象在真实拍摄中物理上不可能出现，确认一条就可以单独定罪。这套方案最终在200条视频上做到了97.5%的总体正确率、零硬性误报。",
"9月13日深夜到14日凌晨，我在新评测集上跑了大规模基线实验，100条视频分十批完成，产出了《外部评测实验报告》，并形成了v58候选提示词。",
]),
("三、发现问题：系统“不敢下结论”", [
"9月23日，我用6条伪造视频做了一次小验证，发现一个严重问题：6条全部被判成“存疑”，没有一条被果断判为“伪造”。其中有一条视频，模型三次独立判断全部指向换脸、证据分也很高，仅仅因为它的“先验分数”是0.46、没到0.70的定罪门槛，就被拦下来变成了存疑。",
"先验分数是计算机视觉分析给出的“可疑程度”评分：0表示完全正常，1表示高度可疑。我们的判决层规定，哪怕模型票型一致，先验分数不到0.70也不能定罪。这个规定让系统太保守了——宁可全部存疑，也不轻易说“这是伪造”。",
"当然，存疑本身不是失败，它是系统诚实的表现：拿不准就说拿不准。但6条全存疑、连证据最充分的一条都不敢定罪，说明天平倾斜过度了——保守的规则当初是为了防误报（防止冤枉真视频）而加的，现在却在伤害检出。到底该加还是该减，不能凭感觉，于是有了后面的消融实验。",
]),
("四、核心工作：消融实验", [
"为了搞清楚判决层到底哪些规则有用，9月27日我做了一次系统的消融实验。消融实验的思想和医学上的对照实验一样：每次只改变一个变量，其他条件全部不变，看结果怎么变。比如要验证“某条规则该不该删”，就让两个版本在其他设置完全相同的情况下，一个有这条规则、一个没有，跑同一批视频来比较。",
"第一步是“零成本重放”。为什么能零成本？因为花钱的部分——调用大模型看视频——在历史上已经花过了，206条视频的模型输出（投票结果、置信度、先验分数）都存在文件里。判决层只是把这些输出套进规则公式，这一步是纯计算，可以无限次重来。我直接复用系统里现成的终裁代码，几十秒就能算完一组变体，而且和真实运行完全一致。这样，十几个“加规则/删规则/改阈值”的版本，一分钱接口费用都不用花就全部算完了。",
"实验结果非常清晰，有三个发现。",
"发现一：判决层20个可调参数里，有5个是“死参数”——配置里写了，但代码根本没用上，或者只在关闭的模式下生效。这些参数是历次“打补丁”留下的：每次发现问题就加一条规则，加着加着就堆了20个，没人回头清理。",
"发现二：真正起作用的只有1个参数，就是定罪背靠阈值（先验分数的最低要求）。把它从0.70降到0.55，在同样零误报的前提下，伪造检出从31条提升到52条，多抓回21条伪造视频。当初这个0.70是为了拦住一条误报案例而设的，但那条案例的先验只有0.434——阈值设到0.45就足够挡住它，0.70属于过度防御。",
"实验里还有一个有趣的现象，说明规则之间会互相“打架”：把定罪闸门从0.70降到0，检出不但没升反而下降了——因为另一条规则规定“控方复核轮”的结论一律只能算存疑，闸门一放低，更多视频流进了那条只能存疑的通道。规则之间的这种互相牵制，正是系统复杂过头的一个证据。",
"发现三最意外：在外部评测集上，20条伪造视频有16条被直接判成“无伪造”。原因出在系统的“分辨率路由”：高清视频默认走“信任模型”的快速通道，不做复查。外部伪造视频恰好大多是高清的，于是大量漏网。更可惜的是，其中有4条的先验分数高达0.55到0.90——量化分析其实已经发现了可疑，却被高清豁免规则放行了。",
]),
("五、v5.8升级与最终验证", [
"根据以上发现，我把系统升级为v5.8，只做三处最小改动：第一，定罪背靠从0.70降到0.55；第二，取消高清分支的冲突豁免，让高先验的高清视频至少进入存疑复核；第三，删掉5个死参数。提示词和调用流程都不动——改动的每一条都有实验数据支撑。",
"随后我设计了最终验证：从我们自己的校准集抽40条（真伪各20）、外部评测集抽60条（真伪各30），共100条视频，让v5.7和v5.8在完全相同的视频上跑对比。为什么两个版本要跑同一批视频？因为大模型每次判断都带一点随机性，只有同一批视频、同一组题目，对比才公平——这就是配对实验的意义。验证结果已经出来了：v5.8 把伪造检出从 0 条提升到 6 条（校准集上从 0 条提升到 5 条，检出率25%），真实误报保持 0 条；此外还有 1 条外部高清伪造从“直接放行”转入了存疑复核。零代价、全提升，升级效果符合实验预期。",
]),
("六、收获与下一步计划", [
"这三周最大的收获是学会了“用实验数据说话”：怀疑系统复杂不是凭感觉，而是逐条验证每个规则的实际贡献。消融实验让我看到，20个旋钮里真正做决定的只有1个，而且它的取值还不是最优的。同时我也体会到严谨的重要性：任何结论都要排除捷径和巧合，比如前面提到的元数据作弊教训，以及配对实验中对随机性的控制。",
"下一步计划：第一，等最终验证出来后，在550+550全量评测集上做正式基准，给系统一个完整可信的成绩单；第二，针对“模型在高质量伪造视频上失明”这个上游瓶颈，设计提示词层的改进实验——这是消融实验无法解决的深水区；第三，修复预处理中唇同步扫描缺失的问题。",
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

total_chars = 0
for head, paras in SECTIONS:
    p = doc.add_paragraph()
    set_font(p.add_run(head), name="黑体", size=13, bold=True, color=(0x1F, 0x4E, 0x79))
    total_chars += len(head)
    for text in paras:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Pt(24)
        p.paragraph_format.line_spacing = 1.4
        set_font(p.add_run(text))
        total_chars += len(text)

doc.save(DOCX_OUT)
print(f"文字稿已生成: {DOCX_OUT}（正文约 {total_chars} 字）")

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
    tf = tb.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text
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
    r.text = "近三周工作汇报"; r.font.size = PPt(48); r.font.bold = True
    r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF); r.font.name = "微软雅黑"
    tb2 = s.shapes.add_textbox(Inches(0.8), Inches(3.5), Inches(11.7), Inches(0.8))
    r2 = tb2.text_frame.paragraphs[0].add_run()
    r2.text = "基于视觉大模型的视频深度伪造（DeepFake）检测"
    r2.font.size = PPt(22); r2.font.color.rgb = PRGB(0xD0, 0xE0, 0xF0); r2.font.name = "微软雅黑"
    tb3 = s.shapes.add_textbox(Inches(0.8), Inches(5.2), Inches(11.7), Inches(0.8))
    r3 = tb3.text_frame.paragraphs[0].add_run()
    r3.text = "汇报人：________    2026年9月27日"
    r3.font.size = PPt(16); r3.font.color.rgb = PRGB(0xE8, 0xE8, 0xE8); r3.font.name = "微软雅黑"

def content(title, items, sub=None, size=18):
    s = prs.slides.add_slide(BLANK)
    title_bar(s, title, sub)
    bullets(s, items, size=size)
    return s

# 1 封面
cover()

# 2 总览
content("三周工作：一个问题 + 三件事", [
    (0, "核心问题：检测系统是不是太复杂了？判决层20个规则，哪些真正有用？"),
    (0, "① 评测集扩容 200 → 1100 条，给系统建更大的“考场”"),
    (0, "② 系统消融实验：逐个关掉规则，用数据回答“哪些有用”"),
    (0, "③ 系统升级 v5.8 并开展最终配对验证"),
    (1, "方法关键词：对照实验思想 + 零成本重放 + 真实API验证"),
], size=20)

# 3 评测集
content("一、评测集建设：200 → 1100 条", [
    (0, "来源：FaceForensics++ 等国际公开数据集（自带官方真伪标签）"),
    (0, "构成：真实 550 条 + 伪造 550 条，伪造覆盖 6 种主流方法"),
    (0, "进度：9/13 建成 100 → 1000 条；9/27 补至 1100 条"),
    (0, "打分指标：检出率（抓出真伪造）/ 误报率（冤枉真视频）/ 存疑率（拿不准）"),
], size=20)

# 4 文档与实验
content("二、文档沉淀与基线实验（9/13—9/14）", [
    (0, "整理两份研究文档：提示词调优回顾、策略与局限性分析"),
    (0, "回顾五阶段提示词演化，确认“做减法”有效"),
    (1, "检测项 21 项 → 14 项，检出率反而 0% → 56%（注意力分散效应）"),
    (0, "外部评测集大规模基线实验：100 条分 10 批，产出实验报告"),
], size=20)

# 5 发现问题
content("三、发现问题：系统“不敢下结论”", [
    (0, "exp6 验证（9/23）：6 条伪造视频，终裁全部“存疑”，检出 0 条"),
    (0, "典型案例：模型三票全投“换脸”、证据分 3 的视频"),
    (1, "仅因先验分数 0.46 < 0.70 定罪门槛，被降为“存疑”"),
    (0, "先验分数 = 计算机视觉给出的可疑程度（0=正常，1=高度可疑）"),
    (0, "结论：判决规则过度保守，需要系统审查"),
], size=20)

# 6 方法
content("四、方法：什么是消融实验", [
    (0, "思想 = 医学对照实验：每次只改变一个变量，其余全部不变"),
    (0, "关键技巧——“零成本重放”"),
    (1, "判决层是纯函数：输入模型票型/置信度/先验 → 输出结论"),
    (1, "历史 206 条视频的输出已存档，离线反复套用不同规则组合"),
    (1, "零 API 费用、几十秒算完一组变体、与真实运行完全一致"),
    (0, "再用真实 API 在同一批视频上配对验证（A/B 实验）"),
], size=20)

# 7 发现一
content("发现一：20 个参数里 5 个是“死参数”", [
    (0, "判决层共 20 个可调参数（阈值、守卫、豁免）"),
    (0, "5 个从未生效："),
    (1, "prosecutor_convict_prior：加载了但代码里从未使用"),
    (1, "4 个仅在“全自动模式”下生效，而当前系统未开启该模式"),
    (0, "启示：规则是“加着加着”堆出来的，需要定期体检"),
], size=20)

# 8 发现二（表格页）
s = prs.slides.add_slide(BLANK)
title_bar(s, "发现二：真正起作用的只有 1 个参数", "定罪背靠阈值（先验最低要求）扫描结果：0.70 被 0.55 严格占优")
rows = [["背靠阈值", "伪造检出(共106)", "真实误报(共100)", "存疑(伪/真)"],
        ["0.70（现状）", "31", "0", "57/5"],
        ["0.65", "41", "0", "47/5"],
        ["0.60", "45", "0", "43/5"],
        ["0.55 ★", "52", "0", "36/5"],
        ["0.45", "66", "3", "22/2"],
        ["0.0", "73", "4", "15/1"]]
tbl = s.shapes.add_table(len(rows), 4, Inches(1.6), Inches(1.9), Inches(10.1), Inches(4.6)).table
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j); c.text = v
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = c.text_frame.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER
        r = pr.runs[0]; r.font.size = PPt(16 if i else 15); r.font.name = "微软雅黑"
        if i == 0:
            r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF)
        elif i == 4:
            r.font.bold = True; r.font.color.rgb = BLUE

# 9 发现三
content("发现三（最意外）：分辨率路由“放行”了伪造", [
    (0, "外部评测集 20 条伪造中 16 条被直接判“无伪造”"),
    (0, "原因：高清视频走“信任模型”快速通道，跳过复查"),
    (1, "外部伪造恰好大多高清 → 大量漏网（“路由击穿”）"),
    (0, "更可惜：其中 4 条先验高达 0.55~0.90"),
    (1, "量化分析其实已发现可疑，却被“高清豁免”规则放行"),
], size=20)

# 10 v5.8
content("五、v5.8 升级：三处最小改动", [
    (0, "① 定罪背靠 0.70 → 0.55（同样零误报，多抓回 21 条伪造）"),
    (0, "② 取消高清分支的冲突豁免（高先验漏检转“存疑”复核）"),
    (0, "③ 删除 5 个死参数"),
    (0, "提示词、调用流程全部不动——改动的每一条都有实验依据"),
], size=20)

# 11 验证
content("六、最终验证结果", [
    (0, "配对设计：100 条视频（校准集 40 + 外部评测集 60），同批对比"),
    (0, "伪造检出：0 条 → 6 条（校准集 0→5、外部 0→1）★"),
    (0, "真实误报：0 条 → 0 条（保持不变）★"),
    (0, "另有 1 条外部高清伪造从“直接放行”转“存疑复核”"),
    (0, "下一步：550+550 全量评测集正式基准"),
], size=20)

# 12 收获
content("七、收获与下一步计划", [
    (0, "收获：学会“用实验数据说话”——怀疑≠空想，逐条验证贡献"),
    (0, "下一步："),
    (1, "全量评测集正式基准（550+550）"),
    (1, "攻克“模型对高质量伪造失明”的上游瓶颈（提示词层实验）"),
    (1, "修复预处理唇同步扫描缺失"),
    (0, "谢谢各位老师！"),
], size=20)

prs.save(PPTX_OUT)
print(f"PPT 已生成: {PPTX_OUT}（共 {len(prs.slides.__iter__.__self__._sldIdLst)} 页）")
