# -*- coding: utf-8 -*-
"""生成课题进展报告精简版：删冗余、留核心，检测流程改为编号+大白话讲解。"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"E:\deepfake\研究文档\20261011_课题进展报告_精简版.docx"

doc = Document()
for sec in doc.sections:
    sec.top_margin = Cm(2.5); sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.4); sec.right_margin = Cm(2.4)

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

def title(text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run(text), name="黑体", size=16, bold=True)

def h1(text):
    p = doc.add_paragraph()
    set_font(p.add_run(text), name="黑体", size=13, bold=True, color=(0x1F, 0x4E, 0x79))
    p.paragraph_format.space_before = Pt(8)

def h2(text):
    p = doc.add_paragraph()
    set_font(p.add_run(text), name="黑体", size=12, bold=True, color=(0x2E, 0x74, 0xB5))
    p.paragraph_format.space_before = Pt(5)

def para(text, indent=True, bold=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.35
    set_font(p.add_run(text), bold=bold)

def table(headers, rows, size=10):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for j, h in enumerate(headers):
        c = t.rows[0].cells[j]; c.text = ""
        set_font(c.paragraphs[0].add_run(h), name="黑体", size=size, bold=True)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            c = t.rows[i].cells[j]; c.text = ""
            set_font(c.paragraphs[0].add_run(str(v)), size=size)
    doc.add_paragraph()

title("视频换脸鉴伪课题进展报告（精简版）")
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run("2026年10月11日"), size=10.5)

h1("一、课题目标（一句话）")
para("用千问大模型加提示词工程，做一套视频换脸检测系统，在自建数据集上实现85%以上的准确率。")

h1("二、检测流程（六步，逐步讲解）")
para("一条视频进系统，就像一件包裹过安检，共六步：", indent=False)

h2("第1步：机器初检（OpenCV预处理）")
para("【做什么】把视频抽成照片（约每2秒一张），在照片里找到人脸，量三样东西：脸清晰吗、脖子清晰吗、脸和脖子差多少。")
para("【为什么】换脸只换脸那一块，所以换脸视频常出现“脸比脖子糊”——机器能量出来，人眼很难看出来。")
para("【产出】一份体检报告，浓缩成一个0到1的分数：先验分数。越接近1越可疑。")

h2("第2步：拍可疑照片（证据图）")
para("【做什么】机器挑出视频里最可疑的几个瞬间截成图片：字幕穿过脸的地方、转头的前后对比、两帧之间的变化。")
para("【为什么】大模型看视频像快进扫一眼，细节会漏；把可疑瞬间单独放大给它看，就像给检查员递放大镜。")

h2("第3步：初筛（温和提问，投1票）")
para("【做什么】把视频、可疑照片、体检报告一起交给大模型，用一张16项检查清单问它：逐项看有没有伪造痕迹，最后给结论。")
para("【为什么叫初筛】这一步用“温和的问法”。温和的问法对真实视频友好（不容易冤枉人），但对伪造容易漏——所以后面还要复检。")

h2("第4步：复检（换问法，投3票取多数）")
para("【做什么】初筛说“无伪造”的视频，换用“控方问法”（激进、专挑毛病）再问3次，取多数票。初筛说“伪造”但把握不大的，换用“辩方问法”（专门帮视频找良性解释）问3次。")
para("【为什么换问法】温和问法漏掉的可疑视频，激进问法容易揪出来；反过来，激进问法冤枉的视频，辩方问法有机会救回来。两种问法互相制衡。")
para("【为什么投3票】大模型每次回答带随机性，问3次取多数，结果更稳。")

h2("第5步：终裁（法官规则）")
para("【做什么】把“票”和“体检报告分”放进一套固定规则，得出三选一：伪造、无伪造、存疑（拿不准，交人工复核）。")
para("【最需要理解的一条规则】控方的票永远不能直接定罪，只能算“可疑警报”。原因：控方问法太激进——实验中它把一批真实视频也全投成了伪造。所以定罪需要更硬的证据组合（比如辩方问法下的票，或第六节讲的融合判定）。")
para("【为什么有这么多“存疑”】系统宁可说“拿不准”，也不冤枉人。所有“存疑”都交人工复核——这是故意的设计。")

h2("第6步：出成绩单")
para("【做什么】结果保存成文件，统计三个数：检出率（真伪造被抓出的比例）、误报率（真视频被冤枉的比例）、存疑率（交人工的比例）。")

h1("三、提示词工程（核心三件）")
para("提示词就是“怎么问大模型”。我们打磨了三套问法：主问法（16项检查清单，日常用）、控方问法（激进，抓漏网）、辩方问法（温和，救冤枉）。")
para("清单里最重要的设计是“证据分级”：美颜滤镜能解释的现象（皮肤光滑、边缘模糊）一律不算伪造证据；光影矛盾、口型对不上这类要两条以上才算数；物理上不可能出现的现象（字幕边缘断裂、转头五官乱跳）一条就能定罪。")
para("外加两条总纪律：无罪推定（默认真实，证据充分才翻案）和美颜辨析（美颜不是伪造）。这两条来自8月一场82%误报的事故。")

h1("四、数据集：1300条真伪样本")
table(["来源", "数量", "技术流派", "高低清"],
      [["自建（流媒体采集+faceswapvideo.io生成）", "200（真100/伪100）", "inswapper系换脸（与FaceFusion同源）", "伪低清/真高清"],
       ["FF++国际基准", "700（真350/伪350）", "六种方法（Deepfakes/Face2Face/FaceShifter/FaceSwap/NeuralTextures/DeepFakeDetection）", "高清"],
       ["angads24社区集", "400（真200/伪200）", "混合，无标注", "偏低清"]])
para("另有 FaceFusion 本机生成的10条高清伪造作专项验证，不进评测集。第三代伪造（扩散模型/音频驱动重演）正式评测暂未覆盖，是下一步扩充方向。")

h1("五、最重要的教训：一次“作弊”的发现与治理")
para("第一阶段系统成绩很好，但复查发现：大模型记住了“低清视频基本都是伪造、高清基本都是真实”的数据集规律，在拿分辨率猜答案；当时的策略还按高低清分了两种标准，把这个假象固定了下来。用FaceFusion本机伪造10条高清伪假验证——全部错判为真实，作弊问题坐实。")
para("治理三招：补高低清混合样本；废除分辨率分标准、统一流程；标签与检测隔离、每改一条规则必须配对验证。治理后成绩变“难看但诚实”——这是做检测必须守住的底线。")

h1("六、调研结论：公开大模型鉴伪能力普遍有限")
para("国内外公开评测一致显示：零样本大模型鉴伪普遍弱于专用检测器，存在“决策崩塌”（看什么都答同一个）等问题；最好成绩（Qwen-3-VL-235B）也只有74.5%。我们用的qwen3-vl-plus在自建集配合提示词工程可达97.5%综合正确率，但对FF++高清伪造检出不足5%——模型对高质量换脸“看得见但认不出”。")

h1("七、融合判定：今天的最新成果")
para("把提示词投票和OpenCV打分组合起来判真假，用网格加二分搜索找到最优规则：物理分不低于0.55，或（三票全投伪造且先验分不低于0.56），判伪造。")
table(["判定规则", "检出(共20)", "误报(共20)", "总正确率"],
      [["只靠提示词票（≥2伪造票）", "20", "13", "67.5%"],
       ["只靠先验分（≥0.55）", "15", "4", "77.5%"],
       ["融合规则", "16", "2", "85.0%"]])
para("融合判定在40条自建样本上总正确率85.0%，正好达到课题目标。诚实说明：样本只有40条，阈值是在这批数据上调的，需要在剩余160条留出集上复测确认。")

h1("八、下一步")
para("① 融合规则在160条留出集复测；② 开发PPG心率特征（换脸破坏面部皮肤微色变，有望把4条漏判捞回来）；③ 评测集扩充第三代伪造样本。", indent=False)

doc.save(OUT)
print("精简版已生成:", OUT)
