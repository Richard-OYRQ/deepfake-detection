# -*- coding: utf-8 -*-
"""生成 5000 字课题进展报告（兼 20 分钟汇报文字稿）+ 13 页 PPT，2026-10-11。"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pptx import Presentation
from pptx.util import Inches, Pt as PPt
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

DOCX_OUT = r"E:\deepfake\研究文档\20261011_课题进展报告_5000字_v2.docx"
PPTX_OUT = r"E:\deepfake\研究文档\20261011_课题进展汇报_20分钟_v2.pptx"

TITLE = "视频换脸鉴伪课题进展报告（2026年10月11日）"
SECTIONS = [
("开场", [
"各位老师好。我是课题组成员，今天汇报我们课题两个月来的进展。先交代课题目标：利用千问大模型和提示词工程，构建一套视频换脸鉴伪系统，在自建数据集上实现85%以上的检测准确率，并形成可复现、可审计的检测流程。两个月走过了三个阶段：8月的误报治理期、9月的策略审视期、10月的验收冲刺期。今天重点汇报五件事：检测系统长什么样、1300条真伪样本从哪来、我们如何发现并治理了检测策略中的一个“作弊”问题、提示词是怎么调优的、以及调研之后对“大模型鉴伪能力到底有多强”的诚实回答。",
]),
("一、检测系统简介：提示词工程、检测策略与 OpenCV 的作用", [
"我们的系统由三条通道组成，可以类比成一场法庭审判：大模型是陪审团，计算机视觉程序是物证鉴定，判决层是法官。",
"第一是提示词工程通道。大模型（千问 qwen3-vl-plus）负责“观看”视频并按提示词检查。提示词体系是“三件套”：主提示词列出16项检测维度（人脸边缘、光影、皮肤纹理、唇形同步、眨眼、微表情、帧间一致性等），并要求模型逐项给出“正常/可疑/异常”判定加时间戳说明；控方提示词是激进版，对伪造敏感度高，负责在复检轮把可疑样本捞出来；辩护人提示词负责对抗复核，逐条给疑似证据找美颜、压缩等良性解释。提示词里还写进了两条重要纪律：无罪推定（默认真实，证据链充分才能翻案）和美颜辨析（美颜滤镜造成的模糊平滑不算伪造证据）——这两条来自8月一场误报事故的教训，后面会讲。",
"第二是检测策略通道（判决层）。模型投完票后，判决层按照一套明确的规则给出三分类结论：伪造、无伪造、或存疑（拿不准，交人工复核）。核心规则包括：伪造定罪需要模型票型和先验分数双重背书；模型说无伪造但先验分数偏高时强制转存疑（防止模型漏看）；置信度不足的一律降为存疑。检测流程上采用“初筛一票加复检三票”的投票机制：每条视频先让大模型初筛一次，多数情况再独立复检三次取多数票，用来压制单次推理的随机波动。需要说明的是，我们后来通过实验认识到：投票只能压制随机性错误，压制不了系统性盲区——模型在高质量伪造上的错误是三票一致的。这套规则的价值在于：系统不轻易冤枉真实视频，宁可说“拿不准”。",
"第三是计算机视觉通道，这里要专门讲清楚 OpenCV 的作用。OpenCV 是一个开源的计算机视觉程序库，在系统里干四件事：第一，人脸检测——用现成的检测器在视频帧里找到人脸位置，这是所有量化分析的前提；第二，清晰度量化——计算面部和颈部区域的图像锐度指标（拉普拉斯方差），生成“面颈清晰度比”；第三，计算先验分数——把清晰度、面颈比等量化指标交给两套统计模型打分，输出0到1的可疑度，这是判决层最重要的输入之一；第四，生成证据图——把遮挡交界、转头过程等关键画面截出来放大，连同纹理热力图一起送给大模型参考。一句话总结分工：OpenCV 负责“量像素”，大模型负责“看语义”，判决层负责“做决定”——三者各补各的盲区。",
]),
("二、数据集构建：1300 条真伪样本的来源与技术流派", [
"目前课题共构建了约1300条真伪样本，分两部分：自建集200条（100真实+100伪造），外部评测集1100条（550真实+550伪造）。这一节专章介绍它们的获取方法和来源，以及技术流派的分类。",
"自建集200条。真实视频100条来自中文流媒体平台的公开短视频（新闻、采访、生活场景，亚洲人脸），采集后做了去重、人脸校验和格式标准化，命名规则为纯数字；伪造视频100条是通过在线换脸网站 faceswapvideo.io 生成的——上传真实视频和另一个人的人脸照片，网站完成换脸。这套网站的技术核心是 inswapper 模型（当前消费级换脸的事实标准，FaceFusion 等主流换脸工具也用它），属于“换脸（换身份）”流派。这个来源意味着我们的自建伪造集代表的是“普通人最容易接触到的伪造方式”，有真实的威胁场景价值。",
"外部评测集1100条。其中伪造550条来自两个公开数据集：FaceForensics++（FF++）350条，这是国际学术界的标准换脸评测数据集，覆盖六种伪造技术流派——Deepfakes（自编码器换脸）、Face2Face（表情迁移）、FaceShifter（高保真换脸）、FaceSwap（图形学换脸）、NeuralTextures（神经纹理重绘）、DeepFakeDetection（早期方法）；angads24 社区数据集200条，为社区收集的换脸样本。真实550条同样来自这两个数据集的真实对照部分。",
"下载方法说明：FF++ 数据集体积大，我们通过 hf-mirror 镜像站用“流式抽取”方式直接从压缩包里抽取需要的视频文件，避免整包下载；angads24 通过镜像站直链批量下载。全部下载脚本记录了固定随机种子和排除名单，保证抽样可复现、新旧实验不重复用同一条视频。",
"高低清构成需要特别说明，因为它和后面要讲的“作弊”问题直接相关：自建集的伪造视频以低清为主（生成网站重编码所致），自建真实视频以高清为主；外部 FF++ 是高清（1080p 重编码），angads24 偏低清。另外，为了验证高清伪造的检测能力，我还用 FaceFusion 在本机额外伪造了10条高清伪假视频用于专项验证——这批样本不进入评测集，专门当“考官”。",
"按技术流派和代际做一个总览：第一代（2017-2019，自编码器/图形学换脸）包括自建集 inswapper 系100条、FF++ 的 Deepfakes/FaceSwap/DeepFakeDetection 约175条、angads24 大部分；第二代（2019-2022，GAN时代）包括 FF++ 的 FaceShifter/NeuralTextures/Face2Face 约175条；第三代（2022至今，扩散模型与音频驱动面部重演，如 FaceFusion/Hallo3 的最新形态）目前只有本地验证用的10条，正式评测集尚未覆盖——这是评测体系当前的缺口，也是下一步扩充方向。",
]),
("三、关键发现：一次“作弊”的发现与治理", [
"这是两个月里最重要的一段经历，我如实汇报。第一阶段检测时，系统成绩看起来非常理想：伪造检出率高、误报率低。但我们复查时发现了一个严重问题：检测程序——特别是大模型——记住了自建检测集的一个规律：低清视频基本都是伪造的、高清视频基本都是真实的。大模型实际上在拿“分辨率”当线索猜答案，而不是在辨别伪造痕迹。更糟的是，当时的检测策略还把这个偏差制度化了：系统按分辨率自动路由，低清视频用激进严格的判定标准，高清视频用宽松的鉴伪标准——结果低清伪造容易被抓、高清真实不容易被冤枉，进一步制造了“成绩理想”的假象。",
"发现过程是这样的：我用 FaceFusion 在本机伪造了10条高清伪假视频，送入检测验证——结果10条全部被错判为真实。这个结果太反常，复查策略代码后确认了上面的问题：这是典型的“数据分布作弊”——系统学到的不是伪造的特征，而是我们数据集的采集偏差。",
"治理分三步。第一步，扩充样本：增加高低清都有真伪视频的样本，用 FF++（高清伪造）和 angads24（低清）平衡分布；第二步，废除分辨率路由：经过降清对照实验和变量隔离实验，确认漏检与分辨率无关、真凶是提示词的敏感度差异，于是把“高清宽松、低清严格”的双重标准统一为一套流程；第三步，结构性防作弊：真伪标签与检测流程严格隔离、元数据屏蔽、所有规则改动必须通过同批视频的配对验证。治理之后，系统成绩变得“难看但诚实”：高清伪造的检出大幅回落，但这是真实的水平。",
]),
("四、提示词调优的过程", [
"提示词是本课题投入最多的部分，经历了五个阶段、二十余轮实验。第一阶段设计了21项检测维度加权重体系，检出率0%——教训是检查项太多会稀释模型注意力，权重对模型无效；第二阶段加到18项，检出率反而降到33%；第三阶段大幅删减到14项，聚焦唇形同步、眨眼、微表情三大生物信号，检出率升到56%；第四阶段配合 OpenCV 量化报告和多次投票，升到86%；第五阶段形成现在的三件套定稿，在自建集上达到97.5%的综合正确率。这段历程的核心经验是“做减法”：提示词不是写得越多越好。",
"调优过程中，我充分利用了 Claude 和 DeepSeek 两位大模型助手的建议：请它们解释检测维度的原理、评审提示词的设计、生成实验和分析脚本、帮助理解统计概念（比如先验概率、消融实验）。但有一条纪律始终没变：它们给的是思路，不是结论——每一条提示词改动和策略调整，最终都以自建数据集上的实测结果为准。举一个例子：助手曾建议尝试让模型“先思考再回答”的推理模式，我们实测后 AUC 只有0.53（接近随机），于是生产环境关闭了它——好建议也要过实验这一关。",
"方法论上还建立了三件工具：消融实验（每次只改一个变量，看结果怎么变）、配对验证（新旧配置跑同一批视频对比，排除模型随机性）、离线重放（把历史检测结果存档后，新策略可以“重放”到旧数据上，一分钱接口费不花就能算完成绩单）。这三件工具让每一次改动都有数据背书。",
]),
("五、调研结论：公开大模型对多源伪假视频的鉴伪能力确实有限", [
"在发现提示词和策略调优进展不理想后，我收集了国内外视频鉴伪大模型的公开评测信息。结论先说：各大模型公司供公开调用的模型，对不同伪造技术流派的伪假视频，鉴别能力确实存在普遍局限。",
"国际上：可解释鉴伪模型 FakeShield 在解释中把真实区域误判为篡改的比例高达36%至41%；跨范式基准 VendorBench-100 中，7个参评视觉大模型的最佳综合分只有0.389（满分1）；TriDF 基准覆盖28个多模态大模型，结论是“感知能力强不等于检测准确率高”；DeepfakeJudge 中表现最好的 Qwen-3-VL-235B 总体准确率也只有74.5%。国内：千问在多个基准中居国产第一梯队，但零样本检测准确率在59%至75%区间；GLM、InternVL、DeepSeek-VL 等各有偏置或数据不足。规律很一致：零样本大模型普遍弱于专门训练的检测器，且存在“决策崩塌”（无论输入什么都倾向同一个答案）的系统性问题。",
"回到我们自己用的千问 qwen3-vl-plus：它在自建集上配合提示词工程能达到97.5%的综合正确率（含人工复核缓冲），但对 FF++ 高清伪造的硬检出率不足5%——模型对高质量换脸存在“看得见但认不出”的失明。我们还发现了9条“不可分样本”：8条伪造和1条真实在所有可测特征上完全重叠，这精确标注了当前模型的能力边界。",
]),
("六、当前状态与下一步计划", [
"基于以上认识，我调整了推进策略：先针对自建伪假视频集进行提示词和检测策略调优，先实现基本的课题目标（自建集85%以上综合正确率），再逐步扩展伪假视频来源。今天的检测成绩如下：自建200条的全量离线统计显示，历史版本检出19条、误报1条、综合正确率94.5%，当前修正版检出0条、误报0条、综合正确率94.5%——零误报的代价是检出归零；刚刚完成的40条最新策略实测进一步印证了这一点：伪造20条零漏判、全部进入存疑池，真实20条零误报（其中14条存疑），综合正确率100%，但硬检出率为0%。这两组数据指向同一个结论：当前系统是一台诚实的筛查机——它保证不漏、保证不冤，但把定罪权完全交给了人工复核。这是一个需要在验收口径上决策的取舍。",
"下一步三件事：第一，开发 PPG 心率特征（换脸只替换面部区域，真人面部皮肤有心率引起的周期性微色变，这是最有望把检出率拉回来的硬测量特征）；第二，自建集全量200条正式验证，出具第一阶段成绩单；第三，扩充第三代伪造样本（FaceFusion/Hallo3 系）进入评测集。",
"最后想请老师们指导三个问题：一是验收口径——综合正确率（存疑不计错）是否适用于课题的85%目标；二是对“自建集优先、外部扩展在后”的推进顺序的意见；三是低成本提升检出率的思路。我的汇报就到这里，谢谢各位老师！",
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
print(f"报告已生成（约 {total} 字）: {DOCX_OUT}")

# ======================= PPT =======================
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLUE = PRGB(0x1F, 0x4E, 0x79)
LBLUE = PRGB(0x2E, 0x74, 0xB5)
GRAY = PRGB(0x40, 0x40, 0x40)
RED = PRGB(0xC0, 0x00, 0x00)
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
    r.font.size = PPt(26); r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF)
    r.font.name = "微软雅黑"
    if sub:
        sb = slide.shapes.add_textbox(Inches(0.55), Inches(0.62), Inches(12), Inches(0.35))
        r2 = sb.text_frame.paragraphs[0].add_run(); r2.text = sub
        r2.font.size = PPt(12); r2.font.color.rgb = PRGB(0xD0, 0xE0, 0xF0); r2.font.name = "微软雅黑"

def bullets(slide, items, x=0.6, y=1.3, w=12.1, h=5.9, size=17):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, (level, text) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = level
        p.space_after = PPt(9)
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
    r.text = "视频换脸鉴伪课题进展汇报"; r.font.size = PPt(46); r.font.bold = True
    r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF); r.font.name = "微软雅黑"
    tb2 = s.shapes.add_textbox(Inches(0.8), Inches(3.5), Inches(11.7), Inches(0.8))
    r2 = tb2.text_frame.paragraphs[0].add_run()
    r2.text = "从一次“作弊”的发现到诚实的能力评估"
    r2.font.size = PPt(22); r2.font.color.rgb = PRGB(0xD0, 0xE0, 0xF0); r2.font.name = "微软雅黑"
    tb3 = s.shapes.add_textbox(Inches(0.8), Inches(5.2), Inches(11.7), Inches(0.8))
    r3 = tb3.text_frame.paragraphs[0].add_run()
    r3.text = "汇报人：________    2026年10月11日"
    r3.font.size = PPt(16); r3.font.color.rgb = PRGB(0xE8, 0xE8, 0xE8); r3.font.name = "微软雅黑"

def content(title, items, sub=None, size=17):
    s = prs.slides.add_slide(BLANK)
    title_bar(s, title, sub)
    bullets(s, items, size=size)
    return s

cover()
content("课题目标与两月总览", [
    (0, "目标：千问大模型 + 提示词工程 → 视频换脸鉴伪系统，自建集 85% 准确率"),
    (0, "8月 治理期：82% 误报事故 → 无罪推定 + 美颜辨析 + 证据分级"),
    (0, "9月 审视期：评测集扩充至 1100 条 + 消融实验 + 发现并治理“作弊”"),
    (0, "10月 验收期：统一流程 + 国内外大模型调研 + 自建集成绩单"),
], size=19)

content("检测系统三通道（法庭类比）", [
    (0, "大模型（陪审团）：16 项检测维度逐项检查 + 三件套提示词"),
    (0, "OpenCV（物证鉴定）：人脸检测 / 清晰度量化 / 先验分数 / 证据图"),
    (0, "判决层（法官）：三分类规则——伪造 / 无伪造 / 存疑（交人工复核）"),
    (0, "【OpenCV 的作用】量像素：找到人脸、算面颈清晰度比、给可疑度打分、截关键证据图"),
    (0, "【大模型的作用】看语义：查边缘、光影、唇形、微表情等 16 项视觉线索"),
], size=19)

content("提示词工程：三件套 + 两条纪律", [
    (0, "主提示词：16 项检测维度，逐项给“正常/可疑/异常”+时间戳"),
    (0, "控方提示词（激进）：复检轮捞可疑样本——对伪造敏感 91%"),
    (0, "辩护人提示词：对抗复核，给疑似证据找良性解释"),
    (0, "纪律① 无罪推定：默认真实，证据链充分才能翻案"),
    (0, "纪律② 美颜辨析：美颜的模糊平滑不算伪造证据（8月事故的遗产）"),
], size=19)

content("数据集：1300 条真伪样本的来源与流派", [
    (0, "自建 200：流媒体平台采集真实 100 + faceswapvideo.io 换脸伪造 100"),
    (0, "外部 1100：FF++ 六方法 350 伪 + angads24 200 伪 + 真实对照 550"),
    (0, "专项验证：FaceFusion 本机伪造 10 条高清伪假（不进评测集，当考官）"),
    (0, "高低清构成：自建伪低清/自建真高清；FF++ 高清；angads24 低清"),
], size=18)

s = prs.slides.add_slide(BLANK)
title_bar(s, "技术流派分类（按代际）")
rows = [["代际", "技术流派", "样本来源与数量"],
        ["第一代", "自编码器/图形学换脸（Deepfakes/FaceSwap/DeepFakeDetection/inswapper 系）",
         "自建 100 + FF++ ~175 + angads24 大部分"],
        ["第二代", "GAN 时代（FaceShifter/NeuralTextures/Face2Face）", "FF++ ~175"],
        ["第三代", "扩散模型/音频驱动重演（FaceFusion/Hallo3 系）", "仅本地验证 10 条 ⚠ 正式评测未覆盖"]]
tbl = s.shapes.add_table(len(rows), 3, Inches(0.9), Inches(1.5), Inches(11.5), Inches(3.8)).table
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j); c.text = v
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = c.text_frame.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER if i == 0 else PP_ALIGN.LEFT
        if not pr.runs:
            continue
        r = pr.runs[0]; r.font.size = PPt(14); r.font.name = "微软雅黑"
        if i == 0:
            r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF)
        if i == 3:
            r.font.bold = True; r.font.color.rgb = RED

s = prs.slides.add_slide(BLANK)
title_bar(s, "核心故事：发现一次“作弊”", "理想成绩的假象是如何被揭穿的")
story = [
    "第一阶段：成绩理想——伪造检出高、误报低",
    "复查发现：大模型记住了“低清≈伪造、高清≈真实”的数据集规律，在拿分辨率猜答案",
    "策略放大了偏差：低清走激进标准、高清走宽松标准 → 假象制度化",
    "决定性验证：FaceFusion 本机伪造 10 条高清伪假 → 全部错判为真实",
    "治理：混合高低清样本 → 实验链废除路由 → 标签隔离/配对验证防再犯",
    "代价：成绩变“难看但诚实”——高清伪造检出大幅回落",
]
tb = s.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(11.7), Inches(5.6))
tf = tb.text_frame; tf.word_wrap = True
for i, t in enumerate(story):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.space_after = PPt(12)
    r = p.add_run(); r.text = ("★ " if i == 3 else "→ ") + t
    r.font.size = PPt(18 if i != 3 else 20); r.font.name = "微软雅黑"
    r.font.color.rgb = RED if i == 3 else (BLUE if i in (0, 5) else GRAY)
    if i in (0, 3, 5):
        r.font.bold = True

content("提示词调优：五阶段历程（Claude + DeepSeek 参与）", [
    (0, "21 项+权重 → 0%；18 项 → 33%；14 项生物信号 → 56%；+OpenCV+投票 → 86%；三件套 → 97.5%"),
    (0, "核心经验：做减法——提示词不是写得越多越好"),
    (0, "调优中利用 Claude/DeepSeek 的建议：原理解释、方案评审、脚本生成"),
    (1, "但纪律不变：助手给思路，实测给结论（例：推理模式建议实测 AUC 0.53，弃用）"),
    (0, "三件工具：消融实验 / 配对验证 / 离线重放（零成本评审）"),
], size=18)

content("调研结论：公开大模型鉴伪能力普遍有限", [
    (0, "FakeShield：解释中把真实区域误判为篡改的比例 36%~41%"),
    (0, "VendorBench-100：7 个视觉大模型最佳综合分仅 0.389（满分1）"),
    (0, "DeepfakeJudge：最好成绩 Qwen-3-VL-235B 准确率 74.5%"),
    (0, "国产第一梯队千问零样本 59%~75% 区间；GLM/InternVL/DeepSeek-VL 各有局限"),
    (0, "共性规律：零样本弱于专用检测器；决策崩塌；“看得见≠认得出”"),
], size=18)

s = prs.slides.add_slide(BLANK)
title_bar(s, "当前成绩单与验收决策", "零误报不是白来的——代价是 19 条检出")
rows = [["策略版本", "伪造检出", "真实误报", "综合正确率"],
        ["8月30日 历史版本", "19/100", "1/100", "94.5%"],
        ["当前修正版", "0/100", "0", "94.5%"]]
tbl = s.shapes.add_table(len(rows), 4, Inches(1.8), Inches(1.7), Inches(9.7), Inches(2.2)).table
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j); c.text = v
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = c.text_frame.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER
        if not pr.runs:
            continue
        r = pr.runs[0]; r.font.size = PPt(16); r.font.name = "微软雅黑"
        if i == 0:
            r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF)
        if i == 2:
            r.font.bold = True; r.font.color.rgb = BLUE
tb2 = s.shapes.add_textbox(Inches(0.8), Inches(4.3), Inches(11.7), Inches(2.4))
tf = tb2.text_frame; tf.word_wrap = True
for k, t in enumerate(["机理：8 条伪造 + 1 条真实在全部可测特征上不可分——能力边界线",
                       "口径：综合正确率（存疑交人工、未犯错）94.5%~100% 达标 85%",
                       "40 条最新实测：零漏判/零误报/综合 100%，检出 0——诚实的筛查机",
                       "突破口已找到：融合判定把检出拉回 80%、总正确率 85%（见下页）"]):
    p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
    p.space_after = PPt(8)
    r = p.add_run(); r.text = "→ " + t
    r.font.size = PPt(16); r.font.name = "微软雅黑"; r.font.color.rgb = GRAY

s = prs.slides.add_slide(BLANK)
title_bar(s, "融合判定：OpenCV × 提示词的组合突破",
          "规则：phys≥0.55 ∨（三票全伪造 ∧ 先验≥0.56）→ 判伪造")
rows = [["判定规则", "检出", "误报", "总正确率"],
        ["纯提示词票（≥2伪造票）", "20/20", "13/20", "67.5%"],
        ["纯先验（≥0.55）", "15/20", "4/20", "77.5%"],
        ["纯物理子分（≥-0.5）", "8/20", "2/20", "65.0%"],
        ["融合规则 ★", "16/20", "2/20", "85.0%"]]
tbl = s.shapes.add_table(len(rows), 4, Inches(1.5), Inches(1.7), Inches(10.3), Inches(3.4)).table
for i, row in enumerate(rows):
    for j, v in enumerate(row):
        c = tbl.cell(i, j); c.text = v
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        pr = c.text_frame.paragraphs[0]; pr.alignment = PP_ALIGN.CENTER
        if not pr.runs:
            continue
        r = pr.runs[0]; r.font.size = PPt(16 if i else 15); r.font.name = "微软雅黑"
        if i == 0:
            r.font.bold = True; r.font.color.rgb = PRGB(0xFF, 0xFF, 0xFF)
        if i == 4:
            r.font.bold = True; r.font.color.rgb = RED
tb2 = s.shapes.add_textbox(Inches(0.8), Inches(5.5), Inches(11.7), Inches(1.5))
tf = tb2.text_frame; tf.word_wrap = True
for k, t in enumerate(["关键：20 条真实里 9 条被控方三票全投伪造、先验全 <0.56——“票∧先验”拦住模型瞎投",
                       "诚实标注：n=40 阈值拟合，需 160 条留出集复测；4 条漏判是 PPG 目标样本"]):
    p = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
    p.space_after = PPt(6)
    r = p.add_run(); r.text = "→ " + t
    r.font.size = PPt(14); r.font.name = "微软雅黑"; r.font.color.rgb = GRAY

content("下一步计划与求助", [
    (0, "① 融合规则在 160 条留出集上复测（确认 85% 真实水平）"),
    (0, "② PPG 心率特征：攻 4 条双低漏判（F16/F32/F39/F43）"),
    (0, "③ 评测集扩充第三代伪造样本（FaceFusion/Hallo3 系）"),
    (0, "求助：验收口径 / 融合规则的适用性 / 低成本提升检出率的思路"),
    (0, "谢谢各位老师！"),
], size=18)

try:
    prs.save(PPTX_OUT)
    print(f"PPT 已更新（{len(prs.slides._sldIdLst)} 页）: {PPTX_OUT}")
except PermissionError:
    alt = PPTX_OUT.replace(".pptx", "_v3.pptx")
    prs.save(alt)
    print(f"原文件被占用，已存为: {alt}（{len(prs.slides._sldIdLst)} 页）")
