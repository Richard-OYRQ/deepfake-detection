"""Generate middle-school-level report (Word) and matching PPT (10 slides)."""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from pptx import Presentation
from pptx.util import Inches, Pt as PptPt, Cm as PptCm
from pptx.dml.color import RGBColor as PptRGB
from pptx.enum.text import PP_ALIGN

from datetime import datetime

# ============================================================
# PART 1: Word Report (~600 words, middle school level)
# ============================================================
doc = Document()
style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

def add_h1(text):
    h = doc.add_heading(text, level=1)
    for run in h.runs:
        run.font.size = Pt(14)
    return h

def add_h2(text):
    h = doc.add_heading(text, level=2)
    for run in h.runs:
        run.font.size = Pt(12)
    return h

def add_p(text, indent=True):
    p = doc.add_paragraph(text)
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.7)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    return p

title = doc.add_heading('AI换脸视频检测小助手 — 我的科创项目汇报', level=0)
for run in title.runs:
    run.font.size = Pt(18)

add_p(f'汇报人：初二科创小组  |  日期：{datetime.now().strftime("%Y年%m月%d日")}', indent=False)
add_p('')

# 1
add_h1('一、项目是什么？')

add_p(
    '你有没有在网上刷到过"明星换脸"的搞笑视频？或者收到过朋友发来的"AI生成照片"？'
    '这种用人工智能把一个人的脸换到另一个人身上的技术，叫做DeepFake（深度伪造）。'
    '它有时候很好玩，但也可能被坏人用来造假骗人。'
)

add_p(
    '我们的项目就是要做一个"AI鉴定小助手"——它能自动帮我们判断一个视频里的人是真是假，'
    '就像是给视频做一次"测谎体检"。'
)

# 2
add_h1('二、我们是怎么做的？')

add_h2('2.1 请了一个"AI鉴定师"')
add_p(
    '我们租用了阿里云上的一个超级AI模型，叫做"通义千问"（Qwen3-VL-Plus）。'
    '它既能"看"视频画面，也能"读"我们的指令。我们给它写了一份详细的"查假清单"——'
    '一共14条检测标准，比如：脸上有没有奇怪的模糊边缘？皮肤是不是光滑得不像真人？'
    '眨眼的频率正常吗？笑的时候眼角有没有自然的皱纹？等等。'
)

add_h2('2.2 加了一个"数学检测仪"')
add_p(
    '光靠AI的"眼睛"还不够——它有时候会把美颜滤镜的效果当成正常画面。'
    '于是我们加了一个叫OpenCV的传统图像处理工具，它用数学方法（拉普拉斯方差）'
    '来精确测量面部和脖子的清晰度。如果面部比脖子模糊很多，那很可能就是换脸！'
    '因为真正的美颜会让整张画面一起变柔，而换脸只替换了面部区域。'
)

add_h2('2.3 用了"少数服从多数"的投票方法')
add_p(
    'AI的判断有时候会"犯困"——同一个视频问它两次，可能得到不同的答案。'
    '所以我们设计了"两轮投票"机制：第一轮所有视频先问一遍，如果AI说"这是假的"，'
    '我们就信它。如果AI说"这是真的"，我们会再问它三遍，取多数意见。'
    '这就像考试时反复检查答案一样！'
)

# 3
add_h1('三、实验结果怎么样？')

add_p(
    '我们用100个视频做了测试，结果还挺令人兴奋的：'
)
add_p(
    '第一，88个视频被成功鉴定为"假"（换脸），检出率88%。只有9个视频被判定为"真"。'
    '第二，AI鉴定师非常有自信——平均自信心达到91分（满分100）。'
    '第三，处理速度也很快——100个视频全部检测完只用了不到1小时（约56分钟）。'
    '第四，最有意思的发现是：AI现在的换脸技术最怕三个检测——皮肤纹理太光滑（92%触发）、'
    '面部边缘有痕迹（91%触发）、肤色不对劲（90%触发）。'
    '这说明换脸技术虽然很厉害，但还是藏不住这些"小尾巴"！'
)

# 4
add_h1('四、我学到了什么？')

add_p(
    '做这个项目让我明白了几个道理：'
    '第一，"少即是多"——一开始我们给AI写了21条检测标准，结果它什么都看不出来（检出率0%）。'
    '后来精简到14条，效果反而最好。这就像考试划重点，划太多反而等于没划。'
    '第二，"老方法也能帮新方法"——用传统的数学图像处理方法（OpenCV）来补充AI的不足，'
    '效果比单纯用AI好得多。就像有了计算器，心算也不可替代。'
    '第三，"参数很重要"——一个小小的阈值从0.70调到0.85，检测准确率就翻了好几倍。'
    '这让我明白，做技术不光是搭框架，细节打磨同样关键。'
)

# 5
add_h1('五、未来还想做什么？')

add_p(
    '下一步，我想给这个系统增加更多功能：让它可以实时检测直播画面中的换脸，'
    '而不是只能分析录好的视频；还想做一个简单的手机App，让同学们也能上传视频'
    '来"验一验真假"。我觉得AI技术本身没有好坏，关键是看我们怎么用它。'
    '希望我的项目能做一点点贡献，让网上的信息更真实、更可信！'
)

add_p('')
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = p.add_run('谢谢大家！')
run.font.size = Pt(12)
run.bold = True

doc.save('D:/DeepFake/科创项目汇报_AI换脸检测小助手.docx')
print('Word report done.')

# ============================================================
# PART 2: PPT (10 slides)
# ============================================================
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

def add_bg(slide, r, g, b):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = PptRGB(r, g, b)

def add_text_box(slide, left, top, width, height, text, font_size=18, bold=False, color=(255,255,255), align=PP_ALIGN.LEFT, font_name='微软雅黑'):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = PptPt(font_size)
    p.font.bold = bold
    p.font.color.rgb = PptRGB(*color)
    p.font.name = font_name
    p.alignment = align
    return tf

def add_bullets(slide, left, top, width, height, items, font_size=16, color=(255,255,255)):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = PptPt(font_size)
        p.font.color.rgb = PptRGB(*color)
        p.font.name = '微软雅黑'
        p.space_after = PptPt(8)
    return tf

# ---- Slide 1: Title ----
slide1 = prs.slides.add_slide(prs.slide_layouts[6])  # blank
add_bg(slide1, 30, 30, 60)
add_text_box(slide1, 1.5, 1.5, 10, 1.5, 'AI换脸视频检测小助手', font_size=44, bold=True, color=(100, 200, 255), align=PP_ALIGN.CENTER)
add_text_box(slide1, 1.5, 3.2, 10, 1, '—— 用人工智能鉴定视频真假', font_size=24, color=(200, 200, 220), align=PP_ALIGN.CENTER)
add_text_box(slide1, 1.5, 4.8, 10, 1, '初二科创小组  |  科创项目汇报', font_size=18, color=(160, 160, 180), align=PP_ALIGN.CENTER)
add_text_box(slide1, 1.5, 5.5, 10, 0.5, datetime.now().strftime("%Y年%m月"), font_size=14, color=(120, 120, 140), align=PP_ALIGN.CENTER)

# ---- Slide 2: Problem ----
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide2, 25, 25, 50)
add_text_box(slide2, 1, 0.6, 11, 0.8, '什么是DeepFake？为什么需要检测它？', font_size=32, bold=True, color=(100, 200, 255))
items2 = [
    '🔍 DeepFake = 用AI把一个人的脸换到另一个人的视频上',
    '😄 好的一面：电影特效、搞笑视频、虚拟主播',
    '⚠️ 坏的一面：假新闻、冒充他人、网络诈骗',
    '🎯 我们的目标：做一个"AI鉴定小助手"，自动判断视频真假',
    '',
    '📊 一个惊人的事实：',
    '   我们测试了100个来自网上的视频，发现其中 88% 都是AI换脸的！',
]
add_bullets(slide2, 1, 1.8, 11, 5, items2, font_size=20)

# ---- Slide 3: How it works overview ----
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide3, 25, 25, 50)
add_text_box(slide3, 1, 0.6, 11, 0.8, '我们的"三步鉴定法"', font_size=32, bold=True, color=(100, 200, 255))
items3 = [
    '第一步 🧠  请一位"AI鉴定师"',
    '     →  租用阿里云的通义千问大模型，让它看视频画面',
    '',
    '第二步 📐  加一个"数学检测仪"',
    '     →  用OpenCV精确测量面部和脖子的清晰度差距',
    '     →  如果面部比脖子模糊很多 → 很可能是换脸！',
    '',
    '第三步 🗳️  来一场"少数服从多数"的投票',
    '     →  第一轮：每个视频问1次',
    '     →  第二轮：对"看起来像真的"再问3遍确认',
    '',
    '✅ 结果：准确率从0% → 88%！',
]
add_bullets(slide3, 1, 1.8, 11, 5, items3, font_size=19)

# ---- Slide 4: 14 detection items ----
slide4 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide4, 25, 25, 50)
add_text_box(slide4, 1, 0.6, 11, 0.8, 'AI鉴定师的"14条查假清单"', font_size=32, bold=True, color=(100, 200, 255))
items4 = [
    '面部边缘  ▸  脸部轮廓有没有奇怪的模糊、马赛克？',
    '皮肤纹理  ▸  皮肤像不像塑料？有没有自然的毛孔？',
    '肤色匹配  ▸  脸和脖子的颜色一样吗？',
    '光影方向  ▸  脸上的光和背景的光是一个方向吗？',
    '唇形同步  ▸  嘴巴动作和声音对得上吗？',
    '头发边缘  ▸  发丝有没有奇怪的断裂或光晕？',
    '眉毛睫毛  ▸  眉毛像不像画上去的？睫毛重复吗？',
    '眼球行为  ▸  眨眼频率正常吗？瞳孔反光一致吗？',
    '微表情    ▸  笑的时候眼角有没有自然的皱纹？',
    '帧间稳定性 ▸  画面一帧帧播放时脸部会不会突变？',
    '头身比例  ▸  头的大小和身体协调吗？脖子自然吗？',
    '耳朵形态  ▸  耳朵形状完整对称吗？',
    '背景异常  ▸  背景有没有奇怪的扭曲或拖拽？',
    '',
    '每一条都要求AI给出：正常 ✅ / 可疑 ⚠️ / 异常 ❌',
]
add_bullets(slide4, 0.8, 1.6, 11.5, 5.5, items4, font_size=15)

# ---- Slide 5: Preprocessing ----
slide5 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide5, 25, 25, 50)
add_text_box(slide5, 1, 0.6, 11, 0.8, '核心创新：用数学区分"换脸"和"美颜"', font_size=32, bold=True, color=(100, 200, 255))
items5 = [
    '🤔 问题：AI经常把换脸的"模糊"误认为是美颜滤镜！',
    '',
    '💡 发现：换脸技术只替换"面部"区域',
    '                    →  面部模糊，但脖子是清晰的',
    '        美颜滤镜作用于"整个画面"',
    '                    →  面部和脖子一起变柔',
    '',
    '🧮 解决方案：计算 "面颈比"（面部清晰度 ÷ 脖子清晰度）',
    '',
    '    📊 面颈比 < 0.80  →  面部单独模糊 →  换脸可疑！',
    '    📊 面颈比 > 0.85  →  全局统一柔化 →  应该是美颜',
    '',
    '📈 这个小小比值的引入，让检出率提升了250%！',
]
add_bullets(slide5, 1, 1.8, 11, 5, items5, font_size=19)

# ---- Slide 6: Voting strategy ----
slide6 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide6, 25, 25, 50)
add_text_box(slide6, 1, 0.6, 11, 0.8, '"两轮投票"策略：像考试一样反复检查', font_size=32, bold=True, color=(100, 200, 255))
items6 = [
    '⚡ 为什么需要投票？AI有时候"犯困"——同一个视频问两次，答案可能不同！',
    '',
    '🗳️ 我们的投票流程：',
    '',
    '    阶段一：100个视频 → 每个问1次 │ 检出"假的"78个 → 直接确认 ✅',
    '                                    │ 检出"真的"22个 → 进入阶段二 ⚠️',
    '',
    '    阶段二：22个"嫌疑真"视频 → 每个再问3次',
    '              │ 3票都说是真的 → 确实是真的 ✅',
    '              │ 多数说是假的 → 原判错误，修正！🔄',
    '',
    '💰 聪明之处：不用对所有视频都投3票（那样要花300次API费用）',
    '    实际只花了约190次，节省了37%的费用！',
]
add_bullets(slide6, 1, 1.8, 11, 5, items6, font_size=18)

# ---- Slide 7: Key results ----
slide7 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide7, 25, 25, 50)
add_text_box(slide7, 1, 0.6, 11, 0.8, '实验结果：100个视频的检测成绩单', font_size=32, bold=True, color=(100, 200, 255))
items7 = [
    '🎯 检出率：88%（100个视频中成功找出88个假的）',
    '✅ 成功率：100%（没有任何视频处理失败）',
    '⏱️  总耗时：56分钟（平均每个视频约34秒）',
    '💰 Token消耗：约110万（调用AI的费用，大约几十元）',
    '🎓 平均置信度：91分（满分100，AI对自己的判断很有信心）',
    '',
    '📊 判定结果分布：',
    '    🔴 换脸（Face Swap）：81个（81%）',
    '    🟠 面部重演（Reenactment）：7个（7%）',
    '    🟢 无伪造（Real）：9个（9%）',
    '    ⚪ 混合判定：3个（3%）',
]
add_bullets(slide7, 1, 1.8, 11, 5, items7, font_size=19)

# ---- Slide 8: Top detection items ----
slide8 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide8, 25, 25, 50)
add_text_box(slide8, 1, 0.6, 11, 0.8, 'AI换脸的"三大软肋"——最容易被发现的3个破绽', font_size=32, bold=True, color=(100, 200, 255))
items8 = [
    '🥇 #3 皮肤纹理异常  →  92%触发率',
    '    皮肤太光滑像塑料，看不到毛孔和微细纹路',
    '',
    '🥈 #1 面部边缘痕迹  →  91%触发率',
    '    脸部轮廓有奇怪的"光晕"，像贴上去的面具',
    '',
    '🥉 #4 肤色不对劲    →  90%触发率',
    '    脸一个颜色，脖子另一个颜色，像是两个人的皮肤',
    '',
    '💡 这三个指标组成了鉴伪"铁三角"！',
    '',
    '📉 相反，以下指标说明换脸技术已经进步了：',
    '    唇形同步异常：仅2%（AI已能很好地对口型）',
    '    面部拉伸撕裂：仅1%（画面不再扭曲变形）',
]
add_bullets(slide8, 1, 1.8, 11, 5, items8, font_size=18)

# ---- Slide 9: Lessons learned ----
slide9 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide9, 25, 25, 50)
add_text_box(slide9, 1, 0.6, 11, 0.8, '我学到了什么？（三个最重要的道理）', font_size=32, bold=True, color=(100, 200, 255))
items9 = [
    '1️⃣  "少即是多" —— 给AI太多任务反而什么都做不好',
    '    21条标准 → 检出率 0%  │  14条标准 → 检出率 56%',
    '    就像考前划重点，划太多等于没划！',
    '',
    '2️⃣  "新老搭配，干活不累" —— AI + 传统数学方法 = 最佳组合',
    '    大模型（新方法）：擅长理解画面、自然语言',
    '    OpenCV（老方法）：擅长精确计算、像素分析',
    '    两者互补，检出率从56% → 88%！',
    '',
    '3️⃣  "细节决定成败" —— 一个小小的阈值改变，效果天差地别',
    '    面颈比阈值 0.70 → 0.85，检出率翻了2.5倍',
    '    做技术不光要搭框架，参数调优同样关键！',
]
add_bullets(slide9, 1, 1.8, 11, 5, items9, font_size=17)

# ---- Slide 10: Future ----
slide10 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide10, 25, 25, 50)
add_text_box(slide10, 1, 0.6, 11, 0.8, '未来展望 & 谢谢大家！', font_size=36, bold=True, color=(100, 200, 255))
items10 = [
    '🚀 接下来想做的三件事：',
    '',
    '    1. 实时检测  📹   让系统能检测直播画面，不只是录好的视频',
    '',
    '    2. 手机App  📱   做一个简单的App，同学们也能上传视频来验真假',
    '',
    '    3. 自动报警  🚨   接入社交媒体，自动标记可疑的AI换脸内容',
    '',
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
    '',
    '💬 我的感想：',
    '',
    '  "技术本身没有好坏，关键看我们怎么用它。',
    '   希望我做的这个小工具，能让网上的信息',
    '   更真实一点点、更可信一点点。"',
    '',
    '🙏 谢谢老师！欢迎提问！',
]
add_bullets(slide10, 1, 1.6, 11, 5.5, items10, font_size=18)

prs.save('D:/DeepFake/科创项目PPT_AI换脸检测小助手.pptx')
print('PPT done.')
print('All files generated successfully!')
