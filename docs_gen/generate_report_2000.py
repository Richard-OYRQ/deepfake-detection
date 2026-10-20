# -*- coding: utf-8 -*-
"""生成约 2000 字精简版课题进展报告：流程分条列举、下载部分从简、无批注。"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"E:\deepfake\研究文档\20261011_课题进展报告_2000字.docx"

doc = Document()
for sec in doc.sections:
    sec.top_margin = Cm(2.5); sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.5); sec.right_margin = Cm(2.5)

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

def para(text, indent=True, bold=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.35
    set_font(p.add_run(text), bold=bold)

def item(text):
    """分条列举项。"""
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.35
    set_font(p.add_run(text))

title("视频换脸鉴伪课题进展报告（精简版）")
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run("2026年10月11日"), size=10.5)

h1("一、课题目标")
para("用千问大模型加提示词工程，构建视频换脸检测系统，在自建数据集上实现85%以上的准确率。")

h1("二、检测流程（六步）")
item("1. 机器初检：把视频抽成照片（每2秒一张），用OpenCV找人脸、量“脸糊不糊、脖子糊不糊、脸和脖子差多少”，得出0到1的先验分数（越接近1越可疑）。换脸只换脸那一块，所以换脸视频常“脸比脖子糊”。")
item("2. 拍可疑照片：机器截出最可疑的瞬间——字幕穿过脸的地方、转头前后对比、两帧之间的变化，放大后随视频一起交给大模型。")
item("3. 初筛：用16项检查清单温和地问大模型一次。温和问法对真实视频友好（不冤枉人），但对伪造容易漏，所以还要复检。")
item("4. 复检：初筛说“无伪造”的，换激进的控方问法问3次取多数；初筛说“伪造”但把握不大的，换温和的辩方问法问3次。两种问法互相制衡；问3次取多数是为了压制大模型单次回答的随机性。")
item("5. 终裁：把票和先验分数放进固定规则，输出三选一：伪造、无伪造、存疑（交人工复核）。关键规则：控方的票永远只算可疑警报、不能直接定罪——因为它太激进，实验里冤枉过真实视频。系统宁可“拿不准”，也不冤枉人。")
item("6. 出成绩单：统计检出率、误报率、存疑率。")

h1("三、提示词工程")
para("提示词就是“怎么问大模型”，我们打磨了三套问法：主问法（16项检查清单）、控方问法（激进，抓漏网）、辩方问法（温和，救冤枉）。16项清单分九大类：面部边缘融合、皮肤纹理、光影、唇形同步、毛发饰品、眼部与微表情、帧间时序、结构与比例、背景，外加两项物理不可能性证据（遮挡破坏、转动连续性）。")
para("清单里最关键的是证据分级：美颜滤镜能解释的现象不算伪造证据；光影矛盾、口型对不上要两条以上才算数；物理上不可能出现的现象（字幕边缘断裂、转头五官乱跳）一条就能定罪。外加两条纪律：无罪推定（默认真实）和美颜辨析（美颜不是伪造）——来自8月82%误报事故的教训。提示词经历了五阶段演化：21项检出0%→14项56%→加量化与投票86%→三件套定稿97.5%，核心经验是“做减法”。")

h1("四、数据集：1300条真伪样本")
para("自建集200条：真实100条来自中文流媒体平台采集；伪造100条用换脸网站faceswapvideo.io生成（核心是inswapper模型，与FaceFusion同源，属于“换身份”流派）。外部评测集1100条：FF++国际基准350真+350伪——伪造覆盖六种技术流派（Deepfakes自编码器换脸、Face2Face表情迁移、FaceShifter高保真换脸、FaceSwap图形学换脸、NeuralTextures神经纹理、DeepFakeDetection早期方法）；angads24社区集200真+200伪。另用FaceFusion本机生成10条高清伪造作专项验证。第三代伪造（扩散模型、音频驱动重演）暂未覆盖，是下一步扩充方向。")

h1("五、最重要的教训：一次“作弊”的发现与治理")
para("第一阶段系统成绩很好，但复查发现：大模型记住了“低清视频基本都是伪造、高清基本都是真实”的数据集规律，在拿分辨率猜答案；当时的策略还按高低清分两种判定标准，把假象固定了下来。用FaceFusion本机伪造10条高清伪假验证——全部错判为真实，作弊坐实。治理三招：补高低清混合样本；废除分辨率分标准、统一流程；标签与检测隔离、改动必须配对验证。治理后成绩变“难看但诚实”。")

h1("六、调研结论：公开大模型鉴伪能力普遍有限")
para("国内外公开评测显示：零样本大模型鉴伪普遍弱于专用检测器，存在“决策崩塌”（看什么都答同一个）问题；可解释鉴伪模型FakeShield的解释有36%~41%把真实区域误判为篡改；跨范式基准中7个视觉大模型最佳综合分只有0.389；DeepfakeJudge最好成绩（Qwen-3-VL-235B）74.5%。我们用的qwen3-vl-plus在自建集配合提示词工程可达97.5%综合正确率，但对FF++高清伪造检出不足5%——对高质量换脸“看得见但认不出”。")

h1("七、融合判定：今天的最新成果")
para("把提示词投票和OpenCV打分组合判真假，网格加二分搜索找到最优规则：物理分不低于0.55，或（三票全投伪造且先验分不低于0.56），判伪造。40条自建样本成绩：检出16/20（80%）、误报2/20（10%）、总正确率85.0%——正好达到课题目标。对照：单靠提示词票总正确率67.5%，单靠先验分77.5%。诚实说明：n=40且阈值在本批数据上拟合，需在160条留出集上复测确认。")

h1("八、下一步")
para("① 融合规则在160条留出集复测；② 开发PPG心率特征（换脸破坏面部皮肤微色变，有望捞回4条漏判）；③ 评测集扩充第三代伪造样本。")

doc.save(OUT)
print("已生成:", OUT)
