#!/usr/bin/env python3
"""生成面向14岁学生的DeepFake检测项目实践指南（5个版本）"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def make_doc():
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(2.54); s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(3.17); s.right_margin = Cm(3.17)
    return doc

def add_title(doc, text):
    t = doc.add_heading(text, level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return t

def add_h(doc, text, level):
    h = doc.add_heading(text, level=level)
    for r in h.runs: r.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    return h

def add_p(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.first_line_indent = Cm(0.74)
    run = p.add_run(text)
    run.font.size = Pt(11); run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    return p

def add_b(doc, text):
    p = doc.add_paragraph(style='List Bullet'); p.clear()
    run = p.add_run(text)
    run.font.size = Pt(11); run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    return p

def add_tip(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.5)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run('💡 ' + text)
    run.font.size = Pt(10); run.font.name = '宋体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    return p

# ============================================================
# VERSION 1: 600 words
# ============================================================
def build_v1():
    doc = make_doc()
    add_title(doc, '利用AI大模型进行DeepFake视频鉴伪检测\n——学生项目实践指南（入门版·600字）')
    info = doc.add_paragraph(); info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.add_run('\n适用对象：初中生（14岁/7年级）\n版本：精简入门').font.size = Pt(10)

    add_h(doc, '一、什么是DeepFake检测？', 1)
    add_p(doc, 'DeepFake（深度伪造）是用AI技术把视频中的人脸换成另一个人的脸。我们的项目就是写一个程序，让AI大模型帮我们自动判断视频是不是被换脸了。')

    add_h(doc, '二、准备工作（4步）', 1)
    add_p(doc, '第1步：在自己的电脑上安装Python（推荐3.11以上版本），下载地址 python.org。安装时勾选"Add Python to PATH"。')
    add_p(doc, '第2步：安装Claude Code编程助手。打开终端（命令提示符），输入 npm install -g @anthropic-ai/claude-code。这是我们的AI编程伙伴。')
    add_p(doc, '第3步：申请千问大模型API密钥。访问阿里云DashScope官网（dashscope.aliyun.com），注册账号后在"API-KEY管理"创建密钥，保存好密钥字符串。')
    add_p(doc, '第4步：在项目文件夹创建.env文件，写入 DASHSCOPE_API_KEY=你的密钥。同时创建config.yaml配置文件和videos文件夹。')

    add_h(doc, '三、编写检测程序', 1)
    add_p(doc, '打开Claude Code，用自然语言告诉它："请帮我写一个Python程序，调用千问视觉大模型分析视频是否被换脸。"说出你的需求，AI会帮你生成代码。核心文件包括：main.py（主程序入口）、config.py（读配置）、client.py（调用API）、processor.py（批量处理）。')

    add_h(doc, '四、设定检测标准（提示词）', 1)
    add_p(doc, '提示词就是告诉AI"怎么检查"。我们的14项标准包括：面部边缘是否模糊、皮肤是否像塑料一样平滑、嘴唇动作是否与声音同步、眨眼是否自然、表情是否僵硬等。提示词写好后放在config.yaml中。')

    add_h(doc, '五、批量检测与优化', 1)
    add_p(doc, '把视频放进videos文件夹，运行 python main.py。程序会自动逐一分析并输出结果。如果发现AI经常判断错误，可以调整提示词或加入OpenCV预处理（检测面部清晰度）。经过多轮调试，检测准确率可从0%提升到86%。')

    add_h(doc, '六、总结', 1)
    add_p(doc, '这个项目让你学会：用AI大模型编程、调用云端API、理解提示词工程、优化算法策略。整个过程就像教AI当一名"视频侦探"——你设定规则，AI执行判断。')

    doc.save('D:/DeepFake/学生指南_V1_入门版_600字.docx')
    print('V1 done')

# ============================================================
# VERSION 2: 1000 words
# ============================================================
def build_v2():
    doc = make_doc()
    add_title(doc, '利用AI大模型进行DeepFake视频鉴伪检测\n——学生项目实践指南（基础版·1000字）')

    info = doc.add_paragraph(); info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.add_run('\n适用对象：初中生（14岁/7年级）\n版本：基础完整').font.size = Pt(10)

    add_h(doc, '一、项目介绍', 1)
    add_p(doc, 'DeepFake是用AI把视频中的人脸替换成另一个人的技术。本项目教你写一个程序，让AI大模型自动分析视频，判断是否被换脸。整个过程用自然语言与AI编程助手（Claude Code）对话就能完成，不需要手写复杂代码。')

    add_h(doc, '二、环境搭建', 1)
    add_h(doc, '2.1 安装Python', 2)
    add_p(doc, '访问 python.org 下载Python 3.11+。安装时务必勾选"Add Python to PATH"。安装完成后打开终端输入 python --version 验证。')
    add_h(doc, '2.2 安装Claude Code', 2)
    add_p(doc, '在终端输入: npm install -g @anthropic-ai/claude-code。这是你的AI编程伙伴，你能用中文和它对话让它写代码。')
    add_h(doc, '2.3 申请千问API密钥', 2)
    add_p(doc, '访问阿里云DashScope（dashscope.console.aliyun.com），注册后创建API-KEY。这是调用千问大模型的"通行证"。')
    add_h(doc, '2.4 项目初始化', 2)
    add_p(doc, '创建项目文件夹，在里面建立.env文件（存密钥）、config.yaml（存配置）、videos文件夹（存放待检测视频）。安装依赖：pip install openai pyyaml python-dotenv opencv-python。')

    add_h(doc, '三、程序结构', 1)
    add_b(doc, 'main.py — 程序入口，解析命令行参数，启动检测流程')
    add_b(doc, 'config.yaml — 配置文件，包括模型名称、API地址、提示词、流控参数')
    add_b(doc, 'src/config.py — 读取和校验配置文件')
    add_b(doc, 'src/client.py — 封装千问API调用，支持本地视频上传')
    add_b(doc, 'src/processor.py — 批量处理调度，控制并发和重试')
    add_b(doc, 'src/preprocessor.py — OpenCV预处理，计算面部清晰度')
    add_b(doc, 'src/formatter.py — 结果格式化为JSON和Markdown')

    add_h(doc, '四、提示词设计', 1)
    add_p(doc, '提示词是检测的核心——它告诉AI从哪些角度检查视频。我们的14项标准覆盖9大类：面部边缘融合（2项）、皮肤纹理（2项）、光影色彩（1项）、唇语同步（1项）、毛发饰品（2项）、眼部微表情（2项）、帧间时序（1项）、结构比例（2项）、背景（1项）。每项给出"正常/可疑/异常"判定。')
    add_p(doc, '提示词调优的关键发现：不是越多越好！21项版检出率0%（注意力分散），精简到14项反而提升到56%。这叫"少即是多"原则。')

    add_h(doc, '五、检测流程', 1)
    add_p(doc, '1. 视频放入videos文件夹。2. 运行 python main.py。3. 程序扫描视频→OpenCV预处理（计算清晰度）→调用千问大模型→输出JSON和Markdown报告。每个视频约需30秒。使用两阶段策略（先快速初筛再精准复检），100个视频检出率可达86%。')

    add_h(doc, '六、优化迭代', 1)
    add_p(doc, '通过多次测试发现：要选择合适的大模型（qwen3-vl-plus最好）、提示词要精简（14项最优）、加入OpenCV预处理可弥补AI对清晰度感知的不足、多次投票可减少随机误判。')

    doc.save('D:/DeepFake/学生指南_V2_基础版_1000字.docx')
    print('V2 done')

# ============================================================
# VERSION 3: 3000 words
# ============================================================
def build_v3():
    doc = make_doc()
    add_title(doc, '利用AI大模型进行DeepFake视频鉴伪检测\n——学生项目实践指南（进阶版·3000字）')

    info = doc.add_paragraph(); info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.add_run('\n适用对象：初中生（14岁/7年级）\n版本：进阶详细').font.size = Pt(10)

    # Ch1
    add_h(doc, '第一章  认识DeepFake与AI鉴伪', 1)
    add_h(doc, '1.1 什么是DeepFake', 2)
    add_p(doc, 'DeepFake（深度伪造）是"Deep Learning"（深度学习）和"Fake"（伪造）的合成词。它利用人工智能技术，将视频或图片中的人脸替换为另一个人的脸，让人误以为目标人物说了某些话或做了某些事。这项技术可以用来制作有趣的换脸视频，但也可能被用于制造虚假信息。因此，学会检测DeepFake是一项非常有价值的技能。')
    add_h(doc, '1.2 AI如何检测DeepFake', 2)
    add_p(doc, 'AI检测DeepFake的原理类似于"找不同"游戏。AI会仔细检查视频的各个方面：人脸边缘是否自然、皮肤是否有真实纹理、嘴唇动作是否与声音同步、眨眼频率是否正常、光影是否一致等等。通过综合分析这些线索，AI可以判断视频是否被篡改。本项目使用的"千问"视觉大模型，能像人类专家一样逐帧审查视频。')

    # Ch2
    add_h(doc, '第二章  编程环境搭建', 1)
    add_h(doc, '2.1 Python环境', 2)
    add_p(doc, 'Python是目前最流行的AI编程语言。访问python.org下载安装包（3.11以上版本），安装时务必勾选"Add Python to PATH"。验证安装：打开终端输入 python --version。')
    add_h(doc, '2.2 Claude Code编程助手', 2)
    add_p(doc, 'Claude Code是Anthropic公司开发的AI编程助手，运行在终端中。安装方法：npm install -g @anthropic-ai/claude-code。启动后，你可以用中文描述需求，AI会自动生成代码、修改文件、运行程序。本项目的全部代码就是通过这种方式完成的。')
    add_h(doc, '2.3 千问大模型API', 2)
    add_p(doc, '千问（Qwen）是阿里巴巴开发的大型AI模型，能"看懂"视频内容。通过DashScope平台（dashscope.console.aliyun.com）注册申请API密钥，即可在程序中使用。API密钥是一串字符（如sk-xxx），相当于调用大模型的"通行证"，需要妥善保管。')
    add_h(doc, '2.4 项目初始化', 2)
    add_p(doc, '创建项目文件夹 D:\\DeepFake\\，结构如下：.env文件存放API密钥；config.yaml存放模型和提示词配置；videos/文件夹存放待检测视频；src/文件夹存放Python源代码（config.py、client.py、processor.py、preprocessor.py、formatter.py）；main.py作为程序入口。安装依赖库：pip install openai pyyaml python-dotenv opencv-python tqdm requests。')

    # Ch3
    add_h(doc, '第三章  编写检测程序', 1)
    add_h(doc, '3.1 配置文件（config.yaml）', 2)
    add_p(doc, '这是整个系统的"控制中心"。包含：api段（模型名称、API地址、密钥、温度参数）、throttle段（最大并发数、每分钟请求上限、重试次数）、output段（输出目录和格式）、videos段（视频目录和提示词）。通过修改配置文件即可切换模型、调整提示词，无需改代码。')
    add_h(doc, '3.2 API客户端（client.py）', 2)
    add_p(doc, '封装了千问大模型的调用逻辑。对于小于18MB的视频，直接将文件编码为Base64传输；大于18MB的视频，先通过DashScope File API上传获取签名URL再引用。统一使用OpenAI兼容接口，只需改base_url即可切换不同厂商的大模型。')
    add_h(doc, '3.3 批量处理器（processor.py）', 2)
    add_p(doc, '负责批量处理调度。核心功能：预处理调用（OpenCV分析）、流控管理（信号量+令牌桶）、重试逻辑（指数退避）、多次投票和两阶段策略。两阶段策略是先对所有视频1票快速初筛，检出"换脸"的确认，初判"无伪造"的再3票复检——兼顾速度和精度。')
    add_h(doc, '3.4 预处理模块（preprocessor.py）', 2)
    add_p(doc, '用OpenCV在API调用前分析视频的清晰度。主要步骤：每隔约1秒提取一帧→用Haar Cascade检测人脸位置→计算面部的拉普拉斯方差（衡量清晰度，值越大越清楚）→同样计算背景和颈部皮肤的清晰度→生成量化报告注入提示词。关键是"面颈比"——如果面部比颈部模糊很多，很可能是换脸；如果面部和颈部同样柔化，更可能是美颜滤镜。')

    # Ch4
    add_h(doc, '第四章  提示词的设计与调优', 1)
    add_h(doc, '4.1 什么是提示词', 2)
    add_p(doc, '提示词（Prompt）就是给AI的"作业要求"。好的提示词让AI知道检查什么、怎么判定、如何输出。本项目最终采用14项检测标准覆盖9大维度。')
    add_h(doc, '4.2 调优故事：从0%到80%', 2)
    add_p(doc, '初始14项版检出率56%。为追求更全面，扩展到21项（增加瞳孔反光、色彩失真、假笑检测等高级维度），结果全部判"无伪造"——检出率0%！原因是检测项太多，AI注意力分散，变得过于保守。果断退回14项后检出率恢复。后来尝试在提示词中描述"面部虚化"让AI检测，被证明无效——AI对像素级模糊不敏感。最终加入OpenCV预处理，用数据说话：面部清晰度32、背景清晰度75、比值0.42，AI终于能准确判断。')
    add_h(doc, '4.3 提示词调优原则', 2)
    add_b(doc, '"少即是多"：精简聚焦比全面覆盖更有效')
    add_b(doc, '量化优于描述：给AI具体数字比文字描述更有效')
    add_b(doc, '数据驱动：用测试结果反馈优化方向')

    # Ch5
    add_h(doc, '第五章  批量检测与结果分析', 1)
    add_h(doc, '5.1 运行检测', 2)
    add_p(doc, '将视频放入videos/文件夹，终端运行 python main.py。程序自动扫描视频文件，逐一调用大模型分析，输出JSON和Markdown格式的结果报告。')
    add_h(doc, '5.2 理解检测结果', 2)
    add_p(doc, '每个视频的结果包含：14项逐项判定表（正常/可疑/异常+时间戳+说明）、异常项统计（如"5/14"）、伪造类型判断（换脸/面部重演/全生成/无伪造）、综合置信度（如"95%"）、关键证据（最有力的3-5条异常）。')
    add_h(doc, '5.3 分析漏检与误报', 2)
    add_p(doc, '检测不完美。有些换脸视频所有指标都正常（零异常），AI无法检出。有些真实视频因为美颜滤镜被误判为换脸。通过对比不同模型（qwen-vl-max的判断比qwen3-vl-plus更激进）和不同策略，可以找到最佳平衡点。')

    # Ch6
    add_h(doc, '第六章  总结与收获', 1)
    add_p(doc, '完成这个项目，你学到了：AI大模型不仅是聊天工具，还能通过API集成到自己的程序里；好的提示词像"好老师"，清晰的要求得到准确的结果；编程不再是写代码，用自然语言和AI对话就能完成复杂项目；数据驱动的迭代思维——做实验、看数据、调整策略、再做实验。')

    doc.save('D:/DeepFake/学生指南_V3_进阶版_3000字.docx')
    print('V3 done')

# ============================================================
# VERSION 4: 5000 words
# ============================================================
def build_v4():
    doc = make_doc()
    add_title(doc, '利用AI大模型进行DeepFake视频鉴伪检测\n——学生项目实践指南（详细版·5000字）')

    info = doc.add_paragraph(); info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.add_run('\n适用对象：初中生（14岁/7年级）\n版本：详细实操').font.size = Pt(10)

    # Ch1
    add_h(doc, '第一章  项目背景与意义', 1)
    add_h(doc, '1.1 DeepFake技术简介', 2)
    add_p(doc, 'DeepFake是"Deep Learning"（深度学习）和"Fake"（伪造）的组合词，指利用人工智能中的深度学习技术，将一个人的脸合成到另一个人的视频或图片中。早期的换脸需要专业软件和大量手工操作，而现在的AI模型可以在几分钟内生成逼真的换脸视频。这项技术既可以用于影视特效、教育等正面场景，也可能被用于制造假新闻、实施诈骗等。因此，开发自动化的DeepFake检测工具具有重要的社会价值。')
    add_h(doc, '1.2 大模型检测原理', 2)
    add_p(doc, '视觉大模型（Vision-Language Model）是一种能同时"看懂"图像和"理解"文字的超大型AI。千问视觉大模型（Qwen-VL）就是其中之一。当我们给它一段视频和一套检测标准（提示词），它会逐帧分析画面中的细节——人脸边缘是否自然、嘴唇动作是否与声音同步、眨眼频率是否正常、光线和阴影是否合理等等——然后综合判断该视频是否被AI换脸篡改。这种方法的优势在于不需要训练专门的检测模型，直接利用大模型的通用理解能力即可。')
    add_h(doc, '1.3 本项目的学习目标', 2)
    add_b(doc, '理解AI大模型的基本概念和API调用方式')
    add_b(doc, '掌握用自然语言与AI编程助手协作开发程序的方法')
    add_b(doc, '学习提示词工程（Prompt Engineering）的基本原理')
    add_b(doc, '理解计算机视觉预处理（OpenCV）的概念')
    add_b(doc, '培养数据驱动的实验思维和迭代优化能力')

    # Ch2
    add_h(doc, '第二章  编程环境搭建详解', 1)
    add_h(doc, '2.1 计算机基础要求', 2)
    add_p(doc, '操作系统：Windows 10/11、macOS或Linux均可。需要联网。建议内存8GB以上。')
    add_h(doc, '2.2 Python安装与配置', 2)
    add_p(doc, '步骤一：访问 https://www.python.org/downloads/，下载Python 3.11或更高版本。步骤二：运行安装程序，务必勾选页面底部的"Add Python to PATH"复选框（这能让系统在任何位置找到Python）。步骤三：安装完成后打开终端（Windows按Win+R输入cmd回车），输入"python --version"，如果显示版本号则安装成功。步骤四：安装pip包管理器（通常随Python自动安装），输入"pip --version"验证。')
    add_h(doc, '2.3 安装必要的Python库', 2)
    add_p(doc, '在终端中逐条输入以下命令：pip install openai（调用千问API的客户端库）、pip install pyyaml（读取YAML配置文件）、pip install python-dotenv（加载.env环境变量）、pip install opencv-python（计算机视觉处理）、pip install tqdm（进度条显示）、pip install requests（HTTP文件上传）。如果下载速度慢，可在命令末尾添加 -i https://pypi.tuna.tsinghua.edu.cn/simple 使用清华大学镜像加速。')
    add_h(doc, '2.4 Claude Code安装与使用', 2)
    add_p(doc, 'Claude Code是AI编程助手。首先安装Node.js（访问nodejs.org下载LTS版本），然后在终端输入 npm install -g @anthropic-ai/claude-code。启动后在浏览器完成账号登录。进入项目文件夹后输入 claude 启动，就可以用中文与AI对话，让它帮你写代码、修改文件、运行程序。')
    add_h(doc, '2.5 千问API密钥申请', 2)
    add_p(doc, '步骤一：访问阿里云DashScope平台 https://dashscope.console.aliyun.com。步骤二：使用阿里云账号登录（没有则注册，支持支付宝实名认证）。步骤三：进入控制台后点击左侧"API-KEY管理"。步骤四：点击"创建API-KEY"，系统生成一串以"sk-"开头的密钥。步骤五：复制并妥善保存密钥（关闭页面后将无法再次查看）。步骤六：在项目文件夹创建.env文件，写入 DASHSCOPE_API_KEY=你的密钥。')
    add_h(doc, '2.6 项目文件夹初始化', 2)
    add_p(doc, '创建 D:\\DeepFake\\ 文件夹，按以下结构初始化：.env（环境变量）、config.yaml（配置文件，内容见后续章节）、videos/（存放待检测的mp4/avi/mkv等视频文件）、src/（存放Python源码）、main.py（程序入口文件）、output/（自动生成，存放检测结果）、logs/（自动生成，存放运行日志）。')

    # Ch3
    add_h(doc, '第三章  程序架构详解', 1)
    add_h(doc, '3.1 整体架构', 2)
    add_p(doc, '程序采用"配置驱动+模块化"设计。main.py读取config.yaml获取全部运行参数，扫描videos目录发现视频文件，然后创建API客户端和流控器，交由VideoProcessor批量处理，最后用Formatter输出JSON和Markdown结果。每个模块职责单一，修改配置无需改动代码。')
    add_h(doc, '3.2 配置文件（config.yaml）说明', 2)
    add_p(doc, 'api段：base_url（千问API地址）、api_key（密钥，可用${ENV_VAR}引用环境变量）、model（模型名称，如qwen3-vl-plus）、max_tokens（单次回复最大字数）、temperature（创造性参数，0.7适中）、timeout（超时秒数）。throttle段：max_concurrent（同时处理几个视频，默认2）、requests_per_minute（每分钟最多几次请求，默认5）、retry_times（失败重试次数，默认3）、vote_count（投票次数，2表示启用两阶段策略）。output段：输出目录和格式（json/markdown/both）。videos段：视频目录和默认提示词。')
    add_h(doc, '3.3 核心源码说明', 2)
    add_p(doc, 'config.py的AppConfig类：from_yaml()方法读取YAML并递归替换${VAR_NAME}环境变量占位符；discover_videos()方法扫描视频目录，自动匹配同名.txt提示词文件；validate()方法校验API密钥、视频目录等关键配置。')
    add_p(doc, 'client.py的QwenClient类：实现三级视频传输策略（<18MB base64内联、>18MB上传DashScope File API获取签名URL）；_call_api()方法组装OpenAI兼容的messages格式，将视频URL和提示词打包发送。')
    add_p(doc, 'processor.py的VideoProcessor类：run_all()实现两阶段策略——阶段一全部视频1票初筛，阶段二对初判"无伪造"的视频3票复检；_process_one()封装预处理调用→API调用→投票逻辑；内置流控和指数退避重试。')
    add_p(doc, 'preprocessor.py：analyze_video()函数实现完整预处理管道——帧采样（均匀间隔，至多16帧）→人脸检测（Haar Cascade取最大人脸）→清晰度计算（拉普拉斯方差）→面颈比分析→多因子评分→生成中文量化报告。关键的阈值包括BLUR_RATIO_THRESHOLD=0.50（面部/背景比值异常线）、is_global_softening面颈比>0.85（全局柔化线）、face_only_blur面颈比<0.80（换脸独虚线）。')

    # Ch4
    add_h(doc, '第四章  提示词工程', 1)
    add_h(doc, '4.1 提示词的本质', 2)
    add_p(doc, '提示词是大模型时代的"编程语言"。写好提示词，就像给一位非常聪明但完全不了解你需求的专家下达任务指令——需要告诉它做什么、怎么做、输出什么格式。差的提示词让AI无所适从，好的提示词让AI产出精准结果。')
    add_h(doc, '4.2 最终14项检测标准', 2)
    add_p(doc, '一、面部边缘融合（#1边缘模糊/锯齿、#2拉伸撕裂）；二、皮肤纹理（#3过度平滑/纹理重复、#4肤色冲突/色差）；三、光影色彩（#5光影矛盾/阴影错误）；四、唇部语音（#6嘴部不同步/唇形僵硬）；五、毛发饰品（#7头发毛边/断层、#8眉毛睫毛/饰品）；六、眼部微表情（#9眼球/眨眼异常、#10微表情缺失/僵硬）；七、帧间时序（#11突变/卡顿/闪烁）；八、结构比例（#12头身比/颈部、#13耳朵扭曲）；九、背景（#14错位/粘连）。')
    add_h(doc, '4.3 提示词调优全历程', 2)
    add_p(doc, '原始14项版检出率56%。扩展到21项（融入YAML规则的高级取证维度）后检出率骤降至0%——这揭示了"注意力稀释效应"：提示词越长，AI越倾向于保守回答。回退14项，检出率恢复。为解决F4视频的面部虚化漏检，新增4项文本描述式虚化检测（"面部像贴上去的"等），结果全部沉默，反而拉低检出率至33%。这证明了纯文本提示词无法引导AI感知像素级视觉异常——需要引入传统CV算法。最终方案：14项提示词+OpenCV量化预处理+判定准则，F1-F10基准集检出率稳定在80%。')
    add_h(doc, '4.4 提示词核心技巧', 2)
    add_b(doc, '给具体标准而非模糊描述（"正常/可疑/异常"三级判定比"有没有问题"更精确）')
    add_b(doc, '要求输出时间戳和说明（"t=3.2s处面部边缘出现模糊"比"有点模糊"更可靠）')
    add_b(doc, '设置判定准则防止AI走极端（"仅一项异常不应直接判定为伪造"）')
    add_b(doc, '量化指标优于主观描述（"面颈比<0.80倾向于换脸"比"看起来很假"有效100倍）')

    # Ch5
    add_h(doc, '第五章  检测流程与策略', 1)
    add_h(doc, '5.1 预处理：AI的"测光表"', 2)
    add_p(doc, '视频进入大模型前，预处理模块先用OpenCV"测光"——计算面部、背景、颈部的清晰度数值。拉普拉斯方差值越大=画面越清晰。如果面部清晰度是背景的50%以下，且比颈部也明显更低，很可能是换脸蒙版虚化。这份量化报告注入提示词末尾，AI就能像侦探拿到化验单一样，结合"视觉感觉"和"数据证据"做综合判断。')
    add_h(doc, '5.2 两阶段投票：又快又准', 2)
    add_p(doc, 'AI大模型有随机性——同一视频两次调用可能结果不同。为解决这个问题：第一阶段，所有视频1票快速筛选，检出"换脸"的直接确认（大多数DeepFake此阶段即被发现）；第二阶段，对初判为"无伪造"的视频3票复检（用多数票压制随机波动）。100视频总成本约190次API调用，比全量3票（300次）节省37%。')
    add_h(doc, '5.3 运行检测与解读结果', 2)
    add_p(doc, '将视频放入videos/文件夹，终端输入 python main.py。程序逐一分析并输出两类结果文件：JSON文件（机器可读，含完整检测文本和token统计）和Markdown文件（人类可读，每视频一个独立报告）。重点关注三个指标：异常项统计（越多越可疑）、伪造类型判断（最终结论）、综合置信度（AI有多确定）。')

    # Ch6
    add_h(doc, '第六章  实验结果与模型选型', 1)
    add_p(doc, '先后测试了4款千问模型。qwen-vl-plus：免费额度易耗尽，判断偏激进，易误报。qwen-vl-max：推理最强但过度标记，把真实视频判为9-12项异常，不适合独立使用。qwen3.6-plus：检出率50%，中规中矩。qwen3-vl-plus（最终采用）：真实视频0%误报、DeepFake检出率80%（F1-F10）、100视频86%，判断风格均衡。模型选择的影响力远超提示词微调——换模型可能带来20%以上的检出率差异。')
    add_p(doc, '100视频两阶段检测结果：总耗时约63分钟，检出86个换脸视频，14个未检出。未检出的视频共同特征是零视觉异常、生物信号全正常、预处理未发现清晰度异常——属于当前方法论的盲区。')

    # Ch7
    add_h(doc, '第七章  总结与展望', 1)
    add_p(doc, '通过本项目，你体验了AI时代的新型编程方式：用自然语言与AI协作而非逐行编写代码。你学习了视觉大模型的工作原理、提示词工程的"少即是多"原则、传统CV与AI模型的互补关系、数据驱动的实验优化方法。未来可以从这些方向继续探索：尝试用MediaPipe替换Haar Cascade提升人脸检测精度；加入频域分析（FFT）检测AI生成图像的纹理伪影；在GPT-4V、Gemini等更多模型上测试方法的泛化能力；构建更大规模的标注测试集系统评估性能。')

    doc.save('D:/DeepFake/学生指南_V4_详细版_5000字.docx')
    print('V4 done')

# ============================================================
# VERSION 5: 10000 words — build on V4 with more depth
# ============================================================
def build_v5():
    doc = make_doc()
    add_title(doc, '利用AI大模型进行DeepFake视频鉴伪检测\n——学生项目实践指南（完整版·10000字）')

    info = doc.add_paragraph(); info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.add_run('\n适用对象：初中生（14岁/7年级）\n版本：完整教程').font.size = Pt(10)

    # ---- Ch1 ----
    add_h(doc, '第一章  走进DeepFake的世界', 1)
    add_h(doc, '1.1 什么是DeepFake', 2)
    add_p(doc, '"DeepFake"是英文"Deep Learning"（深度学习）和"Fake"（伪造）两个单词组合而成的新词。简单来说，就是用人工智能技术，把一个人脸替换成另一个人脸。比如，你可以把自己的脸"贴"到某个电影明星身上，看起来就像你在演电影一样。这项技术最早在2017年左右引起公众关注，当时有人用AI把名人的脸换到了不雅视频中。此后DeepFake技术迅速发展，如今已能生成肉眼难辨真伪的换脸视频。')
    add_p(doc, '换脸视频的制作主要依赖一种叫"自动编码器"或"生成对抗网络"的AI技术。大致原理是：用大量人脸图片训练一个AI模型，让它学会"理解"人脸的样子，然后用另一个模型把学到的脸"画"到目标视频中。随着技术进步，生成的换脸视频越来越逼真——早期的换脸眼睛不自然、边缘锯齿明显，现在的高质量换脸几乎看不出破绽。')
    add_h(doc, '1.2 DeepFake的双面性', 2)
    add_p(doc, '就像任何技术一样，DeepFake也有正面和负面应用。正面应用包括：电影特效（让演员"返老还童"或"复活"已故演员）、教育内容（让历史人物"亲自"讲述历史）、娱乐创意（有趣的换脸App和短视频）。负面应用包括：制造虚假新闻（让政治人物"说"从未说过的话）、网络诈骗（伪造亲友视频借钱）、侵犯肖像权和隐私（未经同意换脸到不当内容）。正因为存在这些风险，学习如何检测DeepFake变得非常重要——我们需要工具来分辨"真的"和"假的"。')
    add_h(doc, '1.3 AI如何成为"视频侦探"', 2)
    add_p(doc, '传统上，检测DeepFake需要人类专家逐帧审查视频——这非常耗时且效率低下。AI大模型的出现改变了这一局面。视觉大模型（Vision-Language Model）是一种特殊的AI，它经过海量图片和视频的训练，学会了"看"和"理解"视觉内容。当你给它一段视频，并告诉它"请检查这个人脸是不是被换过"，它会像一个训练有素的侦探一样，从各个方面仔细分析：人脸边缘是否自然？皮肤纹理是否真实？嘴唇是否和声音同步？光线和阴影是否正确？综合这些线索后，AI会给出一个判断。')
    add_p(doc, '本项目使用的"千问"（Qwen）大模型就是这样的"视频侦探"。它由阿里巴巴开发，能同时处理图像和文字信息。通过OpenAI兼容接口（一种标准的API调用方式），我们的程序可以方便地和它"对话"——把视频和检测要求发过去，它返回分析结果。')

    # ---- Ch2 ----
    add_h(doc, '第二章  搭建你的AI编程工作台', 1)
    add_h(doc, '2.1 你需要准备什么', 2)
    add_p(doc, '硬件方面：一台能上网的电脑（Windows 10/11、macOS或Linux均可），建议8GB以上内存，有至少10GB的可用磁盘空间。因为AI模型运行在云端服务器上，你的电脑不需要很强的显卡。软件方面：Python 3.11以上（免费的编程语言）、Node.js（用来安装Claude Code）、任意文本编辑器（推荐VS Code，免费）或直接用记事本也行。此外还需要一个阿里云账号（注册免费）来申请千问大模型的调用权限。')
    add_h(doc, '2.2 第一步：安装Python', 2)
    add_p(doc, '打开浏览器访问 https://www.python.org/downloads/，网站会自动推荐适合你操作系统的版本。点击黄色的下载按钮。下载完成后双击运行安装程序。最关键的一步：在安装界面底部，一定要勾选"Add Python to PATH"（把Python添加到系统路径）。这一步让你在终端的任何位置都能使用Python命令。选好后点击"Install Now"。安装完成后，按键盘上的Win+R键（Mac按Cmd+空格），输入cmd回车打开命令提示符。在黑色窗口中输入 python --version 并回车。如果屏幕显示"Python 3.11.x"或类似字样，恭喜你安装成功！')
    add_h(doc, '2.3 第二步：安装必要的Python库', 2)
    add_p(doc, 'Python的强大来自丰富的第三方库（别人写好的功能包）。在终端中依次输入以下命令安装我们需要的库：')
    add_b(doc, 'pip install openai — 用于调用千问大模型的官方客户端库')
    add_b(doc, 'pip install pyyaml — 解析YAML格式的配置文件')
    add_b(doc, 'pip install python-dotenv — 从.env文件加载环境变量（如API密钥）')
    add_b(doc, 'pip install opencv-python — OpenCV计算机视觉库，用于视频帧分析和清晰度计算')
    add_b(doc, 'pip install tqdm — 显示终端进度条，让你看到处理进度')
    add_b(doc, 'pip install requests — 发送HTTP请求，用于上传大视频文件')
    add_p(doc, '如果下载速度很慢，可以在命令后面加上 -i https://pypi.tuna.tsinghua.edu.cn/simple 使用国内镜像。例如：pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple。opencv-python这个库比较大（约40MB），用镜像可以快很多。')
    add_h(doc, '2.4 第三步：安装Claude Code', 2)
    add_p(doc, 'Claude Code是Anthropic公司开发的AI编程助手，它运行在终端中，能理解中文指令帮你写代码。首先安装Node.js：访问 https://nodejs.org，下载LTS（长期支持）版本并安装。然后在终端输入 npm install -g @anthropic-ai/claude-code 进行全局安装。安装完成后，在终端输入 claude 启动。首次使用需要登录Anthropic账号。进入你的项目文件夹后运行claude，就可以开始用中文与AI对话编程了。')
    add_h(doc, '2.5 第四步：申请千问API密钥', 2)
    add_p(doc, '访问阿里云DashScope平台 https://dashscope.console.aliyun.com。如果你还没有阿里云账号，点击"注册"，按提示完成注册和实名认证。登录后进入控制台，在左侧菜单找到"API-KEY管理"。点击"创建API-KEY"，系统会生成一串字符（格式类似sk-xxxxxxxxxxxxx）。重要提醒：这个密钥相当于你调用大模型的"密码"，任何人拿到它都可以用你的账号调用AI（产生费用），所以请妥善保管，不要分享给他人，也不要上传到公开的代码仓库。把这个密钥记下来。在项目文件夹创建.env文件，内容为：DASHSCOPE_API_KEY=你的密钥。这样程序就能自动读取。')
    add_h(doc, '2.6 第五步：创建项目结构', 2)
    add_p(doc, '在D盘创建一个名为DeepFake的文件夹（当然也可以在其他位置），然后在其中创建以下子文件夹和文件：.env文件（上面创建的密钥文件）、config.yaml文件（后续会给出内容）、videos文件夹（放待检测视频）、src文件夹（放Python源码）、output和logs文件夹（程序运行后自动生成，可先创建好）。')

    # ---- Ch3 ----
    add_h(doc, '第三章  程序的"骨架"：系统架构', 1)
    add_h(doc, '3.1 程序是怎么工作的', 2)
    add_p(doc, '整个程序像一条流水线：你运行main.py → 程序读config.yaml获取所有设置（用哪个模型、提示词是什么、一次处理几个视频等）→ 扫描videos文件夹发现所有视频 → 创建QwenClient（负责和千问大模型通信）和RateLimiter（控制请求速度） → VideoProcessor开始批量处理（对每个视频：先OpenCV预处理 → 调用千问API → 收集结果） → Formatter把结果整理成JSON和Markdown文件 → 在终端输出汇总统计。')
    add_h(doc, '3.2 各文件的分工', 2)
    add_p(doc, 'main.py是"总指挥"，负责解析命令行参数（如--config指定配置文件、--dry-run只检查不执行），然后启动整个流程。它的代码很短，核心就一个async main()函数。')
    add_p(doc, 'config.yaml是"控制面板"，所有可调整的参数都在这里：用哪个模型、提示词内容、最多同时处理几个视频、重试几次等等。修改配置不需要动代码。config.py里的AppConfig类负责读取、解析和校验这个文件。')
    add_p(doc, 'client.py是"信使"，封装了和千问API的全部通信细节。它用OpenAI的官方Python库（是的，千问支持OpenAI的接口格式，改个网址就行），把视频和提示词打包发送，接收AI的分析结果。')
    add_p(doc, 'processor.py是"流水线主管"，协调整个批量处理过程。它管理并发（同时处理几个视频）、速率（每分钟几次请求）、重试（失败了再试几次）、投票（同一个视频调用多次取多数结果）。两阶段策略也在这里实现。')
    add_p(doc, 'preprocessor.py是"质检员"，在视频送AI之前先做技术分析。它用OpenCV提取帧、找到人脸、计算清晰度数值、判断是"仅面部模糊"还是"全局柔化"，生成一份量化报告——相当于给AI侦探一份化验单。')
    add_p(doc, 'formatter.py是"报告员"，把AI返回的分析结果整理成漂亮的JSON文件和Markdown文件，方便查阅和存档。')

    # ---- Ch4 ----
    add_h(doc, '第四章  "教"AI做检测：提示词工程', 1)
    add_h(doc, '4.1 什么是提示词？为什么它这么重要？', 2)
    add_p(doc, '提示词（Prompt）就是你给AI的"任务说明书"。想象你请了一位非常聪明但完全不了解你工作的专家来帮忙——你给ta的说明越清晰具体，ta的工作质量就越高。提示词就是这个"说明"。在大模型时代，写好提示词是一种核心技能，甚至有一个专门的名字叫"提示词工程"（Prompt Engineering）。')
    add_p(doc, '在DeepFake检测中，提示词决定了AI从哪些角度审查视频。如果提示词太模糊（"帮我看看这个视频有没有问题"），AI可能随便回答。如果提示词太冗长（列了20多个检查点），AI可能注意力分散，每个点都浅尝辄止。好的提示词需要在"全面"和"聚焦"之间找到平衡。')
    add_h(doc, '4.2 最终版14项检测标准详解', 2)
    add_p(doc, '第一大类"面部边缘与融合"（2项）：检查人脸轮廓与背景交界处是否自然——AI换脸常在边缘留下模糊或锯齿痕迹；检查快速转头时面部是否有拉伸变形。')
    add_p(doc, '第二大类"皮肤与纹理"（2项）：检查皮肤是否像塑料一样缺乏真实毛孔和纹理；检查面部肤色和颈部是否一致。')
    add_p(doc, '第三大类"光影与色彩"（1项）：检查脸上的亮面阴影方向是否和环境光源一致——如果鼻子阴影往左但窗户光从右边来，就有问题。')
    add_p(doc, '第四大类"唇部与语音"（1项）：检查嘴唇动作是否和声音节拍同步——AI合成的嘴唇常略微滞后或过于机械。')
    add_p(doc, '第五大类"毛发与饰品"（2项）：检查头发边缘是否有不自然的光晕或断裂；眉毛是否像画上去的、睫毛是否左右完全对称（真人不会完全对称）。')
    add_p(doc, '第六大类"眼部与微表情"（2项）：检查眼球转动和眨眼是否自然（成人正常每分钟眨眼2-10次）；说话时眉毛、脸颊、眼角是否有自然的肌肉联动。')
    add_p(doc, '第七大类"帧间时序"（1项）：逐帧检查面部是否有突然跳动、卡顿或局部闪烁。')
    add_p(doc, '第八大类"结构与比例"（2项）：检查头身比例是否协调、颈部是否有明显的色差线；耳朵形状是否完整对称。')
    add_p(doc, '第九大类"背景"（1项）：检查人物边缘的背景是否有扭曲、错位或被"拖拽"的现象。')
    add_h(doc, '4.3 提示词调优的真实故事', 2)
    add_p(doc, '我们最初的14项版本检出率为56%（9个换脸视频能找出5个）。当时想：多加几个检测项是不是更好？于是参考了一份专业的21条检测规则，把提示词扩展到21项，加入了瞳孔反光不对称、色彩通道失真、假笑无鱼尾纹、帧间水波纹拖影、颈部硬边阴影、背景物体漂移等高级维度。结果大跌眼镜：21项版的检出率变成了0%！所有视频全判"无伪造"。')
    add_p(doc, '经过分析，原因出在"注意力稀释"——提示词太长了，AI要在21个维度间分配注意力，每个都只看个大概，最后选择最安全的回答："正常"。')
    add_p(doc, '果断退回14项后，检出率恢复到56%。后来又针对一个叫F4的视频反复测试——这个视频人脸明显虚化，人眼看一眼就知道是换脸，但AI三轮都判"无伪造100%"。我们在提示词里详细描述了"面部像贴上去的""蒙版羽化带"等概念，AI还是看不出来。最终解决方案不是改提示词，而是加入OpenCV预处理——用程序计算面部清晰度数值，把数据一起给AI。AI终于"看懂"了，F4从0异常变为10项异常检出。')
    add_p(doc, '这个故事告诉我们三个道理：提示词不是越长越好（"少即是多"）；AI对像素级细节的感知有局限，需要传统程序辅助；数据比描述更有说服力。')

    # ---- Ch5 ----
    add_h(doc, '第五章  给AI装"眼睛"：OpenCV预处理', 1)
    add_h(doc, '5.1 为什么AI需要"预处理"', 2)
    add_p(doc, '视觉大模型虽然能"看"图，但它是从整体语义层面理解——就像你看一张照片，你能说出"这是一个微笑的人"，但很难精确说出"左脸清晰度是右脸的83%"。AI也一样，它擅长理解"内容"但不擅长感知"像素"。而DeepFake的一个关键破绽恰恰在像素层面：换脸后通常会对面部做柔化处理（模糊），导致面部清晰度低于背景。这个细微差异人眼能隐约感知，但AI在语义层面会把它解释为"柔光效果"或"美颜滤镜"。预处理模块就是用传统图像处理算法来量化这些AI"看不见"的差异。')
    add_h(doc, '5.2 预处理的核心算法', 2)
    add_p(doc, '清晰度用什么衡量？答案是"拉普拉斯方差"。这个算法计算图像中像素值的变化幅度——变化越大=边缘越多=越清晰。具体步骤：')
    add_b(doc, '1. 帧采样：用OpenCV读取视频，每隔约1秒提取一帧，共4-16帧覆盖视频全程')
    add_b(doc, '2. 人脸检测：用Haar Cascade（一种经典的快速人脸检测算法）在每帧中找到人脸位置')
    add_b(doc, '3. 清晰度计算：分别计算人脸区域和背景区域（四个角）的拉普拉斯方差值')
    add_b(doc, '4. 颈部对比：在人脸下方采样颈部皮肤，计算面颈清晰度比值')
    add_b(doc, '5. 综合评分：根据比值均值、异常帧占比、帧间波动三个指标打分')
    add_p(doc, '最关键的概念是"面颈比"——面部清晰度除以颈部清晰度。真实视频中，即使用了美颜滤镜，面部和颈部的柔化程度通常是一致的。而换脸视频往往对面部做了额外柔化，面部比颈部更模糊——面颈比偏低。这个指标帮助我们区分"美颜滤镜"（整个人都柔化了，面颈比接近1）和"换脸蒙版"（只有面部被柔化，面颈比偏低）。')
    add_h(doc, '5.3 预处理报告的格式', 2)
    add_p(doc, '预处理完成后生成一份中文报告，类似这样："有效检测帧数12帧；面部平均清晰度45.2；背景平均清晰度89.6；面部/背景清晰度比值均值0.50；面颈比0.42；帧间波动系数0.28；清晰度异常帧数8/12；预处理判定：高度可疑。"这份报告自动拼接在提示词末尾，一起发送给AI。')

    # ---- Ch6 ----
    add_h(doc, '第六章  运行检测与理解结果', 1)
    add_h(doc, '6.1 完整的运行流程', 2)
    add_p(doc, '把待检测的视频文件（支持mp4、avi、mkv、mov等格式）复制到videos文件夹。在终端中进入项目文件夹，输入 python main.py。程序会打印欢迎信息（模型名称、视频数量、并发设置等），然后开始逐视频分析。终端会显示进度条（如"阶段一 初筛: 45%|████ | 45/100"）和每个视频的处理结果（✅表示成功、❌表示失败）。所有视频处理完后，程序输出汇总统计（成功X个、失败X个）和结果文件路径。')
    add_h(doc, '6.2 结果文件的解读', 2)
    add_p(doc, 'output文件夹中会生成两种文件：JSON文件（如results_2026-07-05T01-05-56Z.json，文件名包含时间戳）包含所有视频的完整结果，适合程序读取；Markdown文件夹（如run_2026-07-05T01-05-56Z/）中每个视频一个报告文件，适合人类阅读。')
    add_p(doc, '每个视频的检测报告包含四部分：逐项判定表（14行表格，每行有检测项名称、判定结果、时间戳和详细说明）、综合评估（异常项统计如"5/14"、伪造类型判断如"换脸"、综合置信度如"95%"、关键证据列表）、最终结论（1-2句话总结）、以及投票信息（如果是多票策略，显示各票结果）。')
    add_h(doc, '6.3 检测策略的优化历程', 2)
    add_p(doc, 'AI大模型有一个特性：对同一个视频多次调用可能得到不同结果。这有点像你问同一个人同一个问题，不同时间可能得到稍有差异的回答。为了解决这个问题，我们测试了不同的投票策略。1票策略最快但有随机性风险。2票策略更稳定，但如果票数1:1平票，会选置信度高的那个——有时正好选错。3票策略最可靠，但成本最高。最终采用"两阶段策略"：第一阶段所有视频1票快速筛选，检出"换脸"的直接确认；第二阶段对初判"无伪造"的视频进行3票复检。这样既控制了成本，又提升了可靠性。在100个视频的测试中，这个策略成功纠正了3个漏检案例（包括一个叫F6的视频——它在2票时1:1平票漏检，3票复检时全票翻转为换脸）。')

    # ---- Ch7 ----
    add_h(doc, '第七章  模型选型与性能评估', 1)
    add_h(doc, '7.1 测试过的四款模型', 2)
    add_p(doc, 'qwen-vl-plus：千问的增强版视觉模型，提供免费额度，但很快会用完。判断倾向偏激进，容易把真实视频也标为可疑。qwen-vl-max：千问最强版模型，付费使用。推理能力最强，但存在"过度标记"倾向——在测试中把3个真实视频都判为9-12项异常，不适合独立使用。qwen3.6-plus：千问3.6系列增强版，是纯文本模型（不支持视频输入），但碰巧也能处理视频。50%检出率，表现中规中矩。qwen3-vl-plus（最终采用）：千问最新的视觉模型，在真实视频误报率0%的前提下，DeepFake检出率80%（F1-F10基准集）、86%（100视频全量），判定风格均衡。')
    add_h(doc, '7.2 最终性能指标', 2)
    add_p(doc, 'F1-F10基准集（标注的DeepFake视频）：8/10检出（80%），2个未检出（F3和F10，均零异常）。100视频批量检测：86/100检出（86%），14个未检出（均为零或极少异常案例）。真实视频测试（1-10）：0/10误报（0%）。平均每视频耗时约30秒，消耗Token约6,000-12,000。API调用成本约190次/100视频（两阶段策略）。')
    add_h(doc, '7.3 系统局限与未来改进', 2)
    add_p(doc, '当前无法检测"零异常"的最高难度DeepFake——这类视频在所有14个检测项上表现完美，预处理也发现不了异常。Haar Cascade人脸检测器对大角度侧脸和遮挡场景的鲁棒性较差，部分视频会报预处理错误。此外，模型本身的随机性仍然存在，两阶段策略只能减轻不能消除。')
    add_p(doc, '未来改进方向：用MediaPipe或dlib替换Haar Cascade提升人脸检测精度；加入频域分析（傅里叶变换）检测AI生成图像的周期性纹理伪影——这是扩散模型（像Stable Diffusion那样的AI画画工具）的常见痕迹；引入思维链（Chain-of-Thought）提示策略，让AI"先想再答"提高准确性；在GPT-4V、Google Gemini等更多大模型上测试本方案的通用性；建立包含真实和伪造标注的标准测试数据集。')

    # ---- Ch8 ----
    add_h(doc, '第八章  学到的不仅是编程', 1)
    add_p(doc, '这个项目不仅仅是写一个程序，更是一次AI时代的完整实践体验。你学到的核心能力包括：')
    add_b(doc, 'AI协作编程：用自然语言描述需求，让AI生成代码——这将是未来编程的主流方式')
    add_b(doc, '提示词工程思维：学会如何"教"AI做事，理解了"清晰指令>模糊要求"和"少即是多"的原则')
    add_b(doc, '传统算法与AI的互补：理解了为什么AI擅长理解内容但不擅长感知像素，以及如何用传统图像处理算法弥补这个短板')
    add_b(doc, '实验驱动的迭代方法：做实验→看数据→分析原因→调整策略→再做实验——这正是科学研究的方法论')
    add_b(doc, '工程化思维：从配置文件设计到模块化架构，从错误处理到结果格式化，体验了软件工程的全流程')
    add_p(doc, '以上这些能力，远比学会某个具体技术更有价值。AI时代变化很快，今天的热门工具明天可能被替代，但"如何与AI高效协作"和"如何用数据驱动决策"这两项能力，在未来很长一段时间内都将是核心竞争力。')

    doc.save('D:/DeepFake/学生指南_V5_完整版_10000字.docx')
    print('V5 done')


# ================
if __name__ == '__main__':
    build_v1()
    build_v2()
    build_v3()
    build_v4()
    build_v5()
    print('All 5 versions generated!')
