"""Generate 7000-word comprehensive practice report + 28-page PPT for undergrad level.

Covers: Claude Code CLI + DeepSeek-V4-Pro + AI-assisted programming + full detection system.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGB
from pptx.enum.text import PP_ALIGN

from datetime import datetime

def clean(s):
    return s.replace('“', "'").replace('”', "'").replace('‘', "'").replace('’', "'")

# ============================================================
# WORD REPORT
# ============================================================
doc = Document()
style = doc.styles['Normal']
font = style.font; font.name = 'Arial'; font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

def H(doc, text, level):
    h = doc.add_heading(clean(text), level=level)
    sizes = {0: 20, 1: 15, 2: 12.5, 3: 11}
    for r in h.runs: r.font.size = Pt(sizes.get(level, 11))
    return h

def P(doc, text, indent=True):
    p = doc.add_paragraph(clean(text))
    if indent: p.paragraph_format.first_line_indent = Cm(0.7)
    p.paragraph_format.space_after = Pt(5); p.paragraph_format.line_spacing = 1.4
    return p

def T(doc, headers, rows, col_widths=None, fs=9):
    t = doc.add_table(rows=len(rows)+1, cols=len(headers), style='Light Grid Accent 1')
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = clean(h)
        for p in c.paragraphs:
            p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
            for r in p.runs: r.bold = True; r.font.size = Pt(fs)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = t.rows[ri+1].cells[ci]; c.text = clean(str(val))
            for p in c.paragraphs:
                p.paragraph_format.space_before = Pt(1); p.paragraph_format.space_after = Pt(1)
                for r in p.runs: r.font.size = Pt(fs)
    if col_widths:
        for row in t.rows:
            for ci, w in enumerate(col_widths):
                if ci < len(row.cells): row.cells[ci].width = Cm(w)
    return t

def C(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(3)
    r = p.add_run(clean(text))
    r.font.name = 'Consolas'; r.font.size = Pt(8); r.font.color.rgb = RGBColor(0x33, 0x33, 0x44)

# TITLE
H(doc, '基于视觉语言大模型与AI辅助编程的DeepFake视频检测系统开发实践报告', 0)
H(doc, '', 0)
P(doc, f'专业：计算机科学与技术 | 日期：{datetime.now().strftime("%Y年%m月%d日")} | 版本：v3.0', indent=False)
P(doc, '')
P(doc, '摘要：本报告全面记录了基于视觉语言大模型（VLM）的DeepFake视频自动检测系统的完整开发过程。'
   '系统以阿里云百炼平台的Qwen3-VL-Plus为核心推理引擎，结合OpenCV传统计算机视觉预处理实现像素级异常量化，'
   '并通过两阶段多数投票机制压制VLM推理随机性。开发全程采用Claude Code CLI（后端DeepSeek-V4-Pro）进行AI辅助编程，'
   '实践并验证了六种核心交互模式。报告详细阐述了从开发环境搭建与基础设施配置、AI辅助编程交互方法论、'
   '模块化系统架构设计、提示词工程四轮迭代优化到最终100视频批量测试的全流程。'
   '最终系统在测试集上取得了91%的检出率，总结出具有可迁移性的技术方法论框架。')

# ============================================================
# Chapter 1
# ============================================================
H(doc, '第一章 绪论', 1)

H(doc, '1.1 研究背景与选题意义', 2)
P(doc, 'DeepFake（深度伪造）技术是指利用深度生成模型——包括生成对抗网络（GAN）、扩散模型（Diffusion Model）'
   '和自编码器（Autoencoder）——将源人物的面部特征迁移至目标视频中，实现高保真面部替换的技术。'
   '自2017年Reddit用户Deepfakes首次发布换脸视频以来，该技术经历了从实验室算法（FaceSwap、DeepFaceLab）'
   '到消费级应用（SimSwap、Roop）的快速演进。据安全研究机构Sensity AI报告，全球DeepFake视频数量'
   '以年约900%的速度增长，其中96%以上的内容涉及未经同意的面部替换。2023年国内发生多起利用AI换脸'
   '冒充亲友的诈骗案件，单笔涉案金额高达数百万元。在此背景下，开发高效、准确的DeepFake自动检测系统'
   '具有重要的学术价值和社会意义。')
P(doc, '当前DeepFake检测方法分为三大范式：传统图像取证（PRNU噪声、CFA插值、ELA误差分析）、'
   '深度学习二分类（XceptionNet/MesoNet在有标注数据集训练）和视觉语言大模型零样本检测。'
   '本系统属于第三种范式，创新点在于将VLM语义推理与传统CV像素量化相结合，'
   '并通过提示词工程和投票策略实现无需训练数据的实用检测精度。')
P(doc, '此外，本项目在开发方法论上进行了创新探索——系统开发全程采用AI辅助编程范式，'
   '通过Claude Code CLI工具与DeepSeek-V4-Pro大模型进行自然语言交互驱动代码生成与调试，'
   '在实践中总结出六种核心交互模式，为AI辅助软件工程提供了可复用的方法论框架。')

H(doc, '1.2 本报告结构', 2)
P(doc, '第二章介绍AI辅助编程开发环境的搭建与配置过程，包括Claude Code CLI的安装、'
   'DeepSeek-V4-Pro后端的接入以及Python开发环境的配置。第三章系统总结AI辅助编程的交互方法论。'
   '第四章详述大模型API接入与检测系统的核心架构设计，包括六模块架构、OpenCV预处理创新、'
   '流控机制与两阶段投票策略。第五章深入分析提示词工程四轮迭代优化过程。'
   '第六章展示最终检测结果与性能评估。第七章总结技术方法论收获与后续研究方向。')

# ============================================================
# Chapter 2
# ============================================================
H(doc, '第二章 开发环境搭建与基础设施配置', 1)

H(doc, '2.1 硬件与操作系统', 2)
P(doc, '开发设备配置如下：操作系统为Windows 11 Home Chinese Edition (Build 26200)，'
   '处理器AMD Ryzen 7系列，16GB DDR4内存，512GB NVMe SSD。'
   '该配置足以支持Python开发、OpenCV实时视频帧处理以及并发API调用的全部需求。')

H(doc, '2.2 Claude Code CLI：AI辅助编程环境的安装与配置', 2)
P(doc, 'Claude Code CLI是由Anthropic公司推出的命令行AI编程助手工具，是本项目开发的核心生产力工具。'
   '与传统的IDE代码补全（如GitHub Copilot的逐行补全）不同，Claude Code CLI采用对话式交互模式：'
   '开发者通过自然语言描述需求，AI助手理解意图后生成完整代码、执行Shell命令、读写文件并基于运行反馈进行调整。'
   '这种"描述-生成-运行-反馈-迭代"的闭环工作流是整个开发流程的基础。')
P(doc, 'Claude Code CLI的核心能力包括：（1）上下文感知——可自动扫描项目文件结构（通过Glob/Grep/Read工具），'
   '理解代码库全貌后生成上下文一致的代码；（2）工具调用——可直接执行PowerShell命令、读写编辑文件、'
   '运行Python脚本并获取输出；（3）多Agent协作——通过Agent工具将复杂任务分解为多个子Agent并行处理，'
   '如代码探索（Explore Agent）、架构规划（Plan Agent）和通用开发（General-Purpose Agent）；'
   '（4）持久化记忆——通过Memory系统跨会话记录项目知识和用户偏好。')
P(doc, '安装过程如下：通过官方渠道获取Claude Code CLI安装包，配置系统PATH环境变量，'
   '在项目根目录（D:/DeepFake/）下通过命令行启动交互会话。'
   '首次启动时需在设置文件中配置后端大模型的API密钥和端点地址。'
   'Claude Code CLI本身是前端交互界面，实际的代码生成和推理能力由配置的后端大模型提供。')

H(doc, '2.3 DeepSeek-V4-Pro：后端大模型的配置与接入', 2)
P(doc, '本项目使用的后端大模型为DeepSeek-V4-Pro，上下文窗口达1M tokens。'
   'DeepSeek-V4-Pro是DeepSeek公司推出的旗舰级大语言模型，在代码生成、逻辑推理和多语言理解方面表现优异。'
   '1M tokens的超长上下文窗口意味着模型可以一次性加载整个项目的所有源代码文件，'
   '理解全局架构、模块间依赖关系和调用链路，从而生成更准确、上下文一致的代码和方案。')
P(doc, '配置过程可分为三个步骤。第一步，获取DeepSeek API访问权限：在DeepSeek开发者平台注册账号，'
   '完成认证后在控制台创建API Key。第二步，配置Claude Code CLI后端：在CLI的设置文件（settings.json）中'
   '将模型后端指定为DeepSeek-V4-Pro，填入对应的API密钥和API端点地址。'
   '第三步，验证连通性：在项目中发起简单的代码生成请求，确认后端响应正常。'
   '配置完成后，开发者在Claude Code CLI界面中输入的每一次自然语言指令，都会被路由至DeepSeek-V4-Pro后端'
   '进行推理处理，生成结果返回至CLI界面供开发者审查。')
P(doc, '需要特别说明的是，本项目涉及两套完全独立的大模型调用链路，二者不可混淆。'
   '第一套链路为开发工具链：Claude Code CLI（前端交互界面）+ DeepSeek-V4-Pro（后端推理引擎），'
   '用于协助人类开发者编写Python代码、调试错误和生成文档。'
   '第二套链路为检测推理链：Python openai SDK（客户端）+ Qwen3-VL-Plus（阿里云百炼API），'
   '用于对视频画面进行法医学多维度分析并输出换脸判定。')
P(doc, '两套链路的选型逻辑也不相同。开发工具链选择DeepSeek-V4-Pro是因其1M上下文窗口能容纳整个项目代码库，'
   '且代码生成质量在Python领域表现出色。检测推理链选择Qwen3-VL-Plus是因其在视觉理解和中文语义分析方面'
   '达到检出率与误报率的最佳平衡（见第四章模型选型对比）。')

H(doc, '2.4 Python开发环境与依赖管理', 2)
P(doc, 'Python运行时环境选择Python 3.14版本。核心依赖库及其版本如下表所示：')
T(doc,
    ['库名', '版本', '用途', '分类'],
    [
        ['openai', '>=1.0.0', 'OpenAI兼容API客户端封装', 'API通信'],
        ['opencv-python', '4.13.0', 'Haar Cascade人脸检测、拉普拉斯清晰度计算', '图像处理'],
        ['numpy', '2.4.6', '数值计算与数组操作', '科学计算'],
        ['PyYAML', '6.0.3', 'YAML配置文件解析', '配置管理'],
        ['tqdm', '4.68.1', '终端进度条可视化', '用户界面'],
        ['colorama', '0.4.6', '控制台彩色文本输出', '用户界面'],
        ['python-dotenv', '1.2.2', '.env环境变量加载', '配置管理'],
        ['python-docx', '最新', 'Word文档生成', '报告输出'],
        ['requests', '最新', 'DashScope文件上传API调用', 'HTTP通信'],
    ],
    col_widths=[3, 1.5, 5, 2]
)
P(doc, '所有依赖通过pip包管理器一键安装，安装过程顺利，未出现版本冲突或兼容性问题。')

H(doc, '2.5 项目工程目录结构', 2)
P(doc, '系统采用模块化分层架构设计。目录结构如下：')
C(doc, 'D:/DeepFake/')
C(doc, '  main.py              -- Entry point, CLI parsing, orchestration')
C(doc, '  config.yaml          -- Global config (API, model, throttle, prompt)')
C(doc, '  src/')
C(doc, '    config.py          -- Config layer: YAML+ENV, video discovery (7 formats)')
C(doc, '    preprocessor.py    -- OpenCV: frame sampling, face detection, Laplacian sharpness')
C(doc, '    client.py          -- Qwen API wrapper, 3-tier video upload strategy')
C(doc, '    processor.py       -- Async scheduler, retry logic, two-stage voting')
C(doc, '    rate_limiter.py    -- Token Bucket: concurrency + RPM dual control')
C(doc, '    formatter.py       -- JSONL incremental + JSON aggregate + Markdown reports')
C(doc, '  videos/              -- Input video directory')
C(doc, '  output/              -- Detection result output')
C(doc, '  logs/                -- Runtime logs')

# ============================================================
# Chapter 3
# ============================================================
H(doc, '第三章 AI辅助编程交互方法论', 1)

H(doc, '3.1 AI辅助编程的整体工作流程', 2)
P(doc, '本项目的完整开发过程采用"自然语言驱动大模型编程"的交互范式。开发者在Claude Code CLI界面中以自然语言'
   '描述需求（如"请结合21条.yml完善鉴伪提示词"），DeepSeek-V4-Pro后端理解需求后读取项目相关文件、'
   '分析代码上下文、生成代码或修改方案，开发者审查后确认执行。程序运行后，开发者将结果（日志、检出率、'
   '具体漏检案例等量化数据）反馈给AI，AI基于数据调整方案，进入下一轮迭代。整个开发过程累计交互百余轮、'
   '代码变更数十次、运行测试十余轮，在16天开发周期内从零搭建到稳定运行。')
P(doc, '开发者和AI形成了一种"策略者-执行者"的协作模式——人类负责确定技术方向、提供判断基准（真实标签、'
   '量化评估指标）和做出关键决策；AI负责方案生成、代码实现、数据分析和迭代优化。'
   '两者的能力互补而非替代：AI在方案生成和代码实现上效率远超人类，但在没有Ground Truth（真实标签）'
   '的情况下难以判断方案优劣；人类擅长基于领域知识和实验结果做出判断，但在代码编写的速度和规模上不及AI。')

H(doc, '3.2 六种核心交互模式', 2)
P(doc, '经过对百余轮交互记录的梳理分析，我们总结出以下六种核心交互模式，它们在项目的不同阶段'
   '发挥了关键作用，构成了可复用的AI辅助编程方法论框架。')

P(doc, '模式一：递进式需求分解（Progressive Requirement Decomposition）。将复杂任务分解为递进子任务链，'
   '每步聚焦单一目标，前一步的输出作为后一步的输入。表述模板："第一步[基础操作]；第二步[中等操作]，'
   '基于第一步的结果；第三步[复杂操作]，综合前两步成果"。本项目典型应用为提示词调优过程：'
   '"先将提示词退回到14项 -> 然后试试增加预处理方案 -> 最后调整预处理阈值"。'
   '优势在于降低单次交互复杂度，每步可独立验证，出错时快速定位问题环节。')

P(doc, '模式二：假设-验证循环（Hypothesis-Verification Loop）。提出可验证假设 -> 执行对比实验 -> '
   '基于数据确认或推翻假设 -> 迭代优化。本项目最经典的案例是F4视频虚化盲区问题的诊断：'
   '观察到F4人眼可见面部虚化但模型三轮判定"无伪造100%" -> '
   '提出假设"VLM对像素级清晰度差异的感知存在先天盲区" -> '
   '设计验证"新增4项面部区域一致性文本检测指标（纯提示词层面）" -> '
   '实验结果"4项指标全测试集零触发，检出率反降至33%" -> 假设成立 -> '
   '结论"必须引入传统CV预处理而非依赖纯文本提示词"。'
   '这一发现直接决定了系统技术路线的走向，是项目最重要的转折点。')

P(doc, '模式三：数据驱动的策略调整（Data-Driven Strategy Adjustment）。以标注数据为基准，'
   '量化评估系统性能，针对性调整策略参数。表述模板："当前性能：真实集误报率X%，伪造集检出率Y%。'
   '主要遗漏：[具体案例]。优化目标：保持误报率<=X%前提下将检出率提升至>=Z%。'
   '调整方向：参数A从M->N"。在本项目中体现为面颈比阈值调优——从标注数据（F1-F10为伪造视频）出发，'
   '经过七轮阈值调整将F1-F10检出率从2/10提升至7/10。')

P(doc, '模式四：探索-评估-决策（Explore-Evaluate-Decide）。先提供多个可选方案让AI分析优劣，'
   '再基于评估结果做出决策，最后执行选定方案。典型应用为投票策略选型：'
   '提出方案A（全量2票，200次调用，可能1:1平票）、方案B（全量3票，300次调用，打破平票）、'
   '方案C（两阶段：1票初筛+对无伪造3票复检，约190次调用），AI分析各方案优劣后推荐方案C，用户确认实施。')

P(doc, '模式五：锚定提问（Anchored Inquiry）。给出具体的参照基准或量化对比数据，'
   '让AI基于精确上下文进行分析而非泛泛而谈。如："F6为什么没有检出（4项异常+投票1:1平票）？'
   '如果改为两票，F6能被检出吗？"——通过提供具体检测结果和异常计数作为锚点，'
   '引导AI聚焦于平票机制缺陷的精准诊断而非泛泛分析。')

P(doc, '模式六：元认知引导（Metacognitive Guidance）。让AI对自己的输出进行自我审查和主动提出改进方向。'
   '如用户提问"提示词工程还有优化空间吗？"，AI主动提出思维链推理、对抗性审查、关键帧策略和量化锚定四个方向供选择。'
   '这种模式适用于打破思维惯性、探索未知优化方向，是"人机共创"的最高境界。')

H(doc, '3.3 高级交互策略', 2)
P(doc, '除六种核心模式外，本项目还提炼出四条高级交互策略。'
   '（1）分层沟通——区分战略级（做什么、为何做）和战术级（怎么做、参数是多少），先达成战略共识再下放战术执行。'
   '（2）增量验证——每完成一个可验证的变更立即运行测试确认效果，避免多目标同时修改导致问题难以追溯。'
   '（3）定量反馈——用"检出率从56%降至33%，F4仍未检出"替代"效果不好"的模糊表述，'
   '量化数据是AI分析和调整的最有效输入。'
   '（4）真值注入——有标注数据时尽早告知AI真实标签（如"F2是被AI换脸后的视频"），'
   '让AI基于Ground Truth进行自我校准，这是提升AI输出质量的最有效手段。')

H(doc, '3.4 AI辅助编程关键提示词汇编', 2)
P(doc, '项目开发过程中使用的关键编程提示词按功能阶段整理如下：')
T(doc,
    ['阶段', '典型提示词', '产出与价值'],
    [
        ['系统摸底', '我现在配置文件中调用的千问的哪个大模型', '快速了解当前系统状态'],
        ['配置变更', '请将model改为qwen3-vl-plus', '模型切换，4次变更0错误'],
        ['提示词工程', '请结合21条.yml进一步完善一下鉴伪提示词', 'v2.0 21项版提示词'],
        ['版本回退', '请将提示词还原为前一个版本', 'v3.0 14项版，检出率0%->56%'],
        ['问题诊断', '第4个视频人脸虚化，大模型从哪方面可以强化检测', '虚化盲区根因分析'],
        ['方案实施', '按方案C进行更新 / 试着增加关键帧策略和量化锚定', 'v3.1方案执行'],
        ['预处理开发', '先将提示词退回到14项，然后试试增加预处理方案', 'preprocessor.py创建'],
        ['Bug修复', '试着修复一下Haar Cascade的兼容性问题吧', 'scaleIdx断言失败修复'],
        ['阈值调优', '调整预处理阈值减少全局柔化误判', '面颈比阈值收敛至0.85'],
        ['投票测试', '使用3次投票单独跑一下F3、F6、F10', '3票验证，F6 3:0全票检出'],
        ['策略设计', '1票初筛+对无伪造3票复检，你觉得合理吗？', '两阶段架构确定'],
        ['漏检分析', 'F6为什么没有检出？', '平票机制诊断与修复'],
        ['真值反馈', 'F2是被AI换脸后的视频 / 新视频1-10都是真实的', '模型自我校准'],
        ['报告生成', '请编写5000字研究报告（含环境安装/API申请/提示词调优）', '多版本Word/PPT报告生成'],
    ],
    col_widths=[2, 5.5, 4]
)

H(doc, '3.5 交互效率与质量控制', 2)
P(doc, '通过对比不同交互方式的效果，我们形成了以下交互效率认知：'
   '开放式提问单轮产出和准确性最低，仅适合探索初期；'
   '模板化提问适合方案设计阶段，产出和准确性中等；'
   '锚定+数据驱动的交互方式单轮产出和准确性最高，适合调优迭代阶段；'
   '假设-验证循环在问题诊断和根因分析场景中准确性最高。'
   '关键质量控制原则包括：一次只做一件事（多目标同时修改导致交互混乱），'
   '定量反馈替代模糊感受（数据锚定AI的分析方向），'
   '以及及时的Ground Truth注入（真实标签是AI自我校准的最有效参照）。')

# ============================================================
# Chapter 4
# ============================================================
H(doc, '第四章 大模型API接入与系统架构设计', 1)

H(doc, '4.1 检测模型选型：四款千问模型的系统对比', 2)
P(doc, '检测引擎需选用具备视频理解能力的视觉语言大模型（VLM）。经调研选择阿里云百炼平台（DashScope）'
   '的通义千问视觉模型系列。该平台提供OpenAI兼容的REST API接口（Endpoint: dashscope.aliyuncs.com/'
   'compatible-mode/v1），可直接使用openai Python SDK调用，极大简化了客户端集成。'
   'API Key申请流程：阿里云账号注册 -> 实名认证 -> 百炼控制台创建AccessKey -> 配置到config.yaml。')
P(doc, '我们对四款千问视觉模型在F1-F10基准集上进行了系统对比评估：')
T(doc,
    ['模型', 'Recall(F1-F10)', '误报倾向', '平均延迟', '综合判定'],
    [
        ['qwen-vl-plus', 'N/A (额度耗尽)', '—', '—', '不可用'],
        ['qwen-vl-max', '100% (过度敏感)', '高 (9-12项异常)', '~40s', '过度激进, 不宜独立使用'],
        ['qwen3.6-plus', '~50%', '低', '~35s', '中等偏保守, 备选'],
        ['qwen3-vl-plus', '80%', '0%', '~35s', '最优平衡 - 最终采用'],
    ],
    col_widths=[3, 2.5, 3, 1.5, 4]
)
P(doc, '核心选型经验：在VLM的工程化应用中，模型能力并非越强越好。qwen-vl-max虽为旗舰模型，'
   '却因检出敏感度过高（真实视频被误标9-12项异常）不宜独立用于生产环境。'
   'qwen3-vl-plus以适中的敏感度实现了检出率（80%）与误报率（0%）的均衡最优，'
   '验证了"均衡性比单项指标更重要"的工程化选型原则。')

H(doc, '4.2 系统架构总览与数据流', 2)
P(doc, '系统采用六模块分层架构。以下为整体数据流逻辑图：')
C(doc, '  config.yaml + .env  -->  AppConfig.load()  -->  discover_videos()')
C(doc, '                              |')
C(doc, '                              v')
C(doc, '  VideoProcessor.run_all()  (Two-Stage Voting Orchestrator)')
C(doc, '    |')
C(doc, '    +-- For each video task:')
C(doc, '    |    1. preprocessor.analyze_video()  -->  Laplacian sharpness report')
C(doc, '    |    2. prompt += preprocess_report   -->  Augmented 14-item prompt')
C(doc, '    |    3. rate_limiter.acquire()        -->  Token Bucket: wait for token')
C(doc, '    |    4. client.call(task)             -->  Qwen3-VL-Plus API')
C(doc, '    |    5. rate_limiter.release()        -->  Release semaphore slot')
C(doc, '    |    6. formatter.save_one(result)    -->  JSONL incremental write')
C(doc, '    |')
C(doc, '    +-- Stage 1: all videos x 1 vote  |  Stage 2: NoForgery x 3 votes')
C(doc, '    |')
C(doc, '    v')
C(doc, '  formatter.output_results()  -->  JSON aggregate + Markdown per-video')

P(doc, '六模块职责分工如下：config.py负责YAML配置解析、${ENV}环境变量递归替换和视频自动发现'
   '（支持mp4/avi/mkv/mov/webm/flv/wmv共7种格式），并为每个视频自动匹配同名txt提示词或回退默认提示词。'
   'preprocessor.py在API调用前对每个视频执行OpenCV面部清晰度量化分析。'
   'client.py封装千问OpenAI兼容API调用，实现三级视频传输策略的自动降级。'
   'rate_limiter.py基于令牌桶算法实现并发（Semaphore=2）与频率（RPM=5）双重控制。'
   'processor.py负责asyncio异步任务编排、指数退避重试（delay=2^attempt, max=3）'
   '和两阶段多数投票逻辑。formatter.py提供JSONL增量持久化、JSON聚合报告和Markdown逐文件详细报告。')

H(doc, '4.3 OpenCV预处理模块：核心技术创新', 2)
P(doc, '预处理模块（preprocessor.py）是本系统区别于纯VLM方案的核心技术创新点。'
   '其设计动机源于v3.1的关键实验发现：纯文本提示词无法让VLM感知像素级清晰度异常。'
   '核心思路转变——不再试图用文字让AI"看到"清晰度差异，而是用数学直接计算清晰度数值，把数字告诉AI。')
P(doc, '预处理算法流程包括五个步骤。第一步——视频帧采样：cv2.VideoCapture读取视频，'
   '获取CAP_PROP_FRAME_COUNT和CAP_PROP_FPS计算时长，以均匀时间间隔采样min(16, max(4, total_frames // int(fps * 2)))个关键帧。'
   '第二步——人脸检测：使用Haar Cascade级联分类器（haarcascade_frontalface_default.xml），'
   '参数为scaleFactor=1.1、minNeighbors=5、动态minSize调整，多人脸时取面积最大者。'
   '对大尺寸帧（>1920px）自动缩放处理以避免内存问题，检测失败时降级为宽松参数重试（scaleFactor=1.2, minNeighbors=3）。'
   '第三步——三区域清晰度计算：对人脸ROI、背景四角采样区（避开人脸）和颈部皮肤区（面部下方0.3-0.8倍人脸高度）'
   '分别计算拉普拉斯方差（cv2.Laplacian(gray, CV_64F).var()），值越大表示画面越清晰。'
   '第四步——多因子评分：比值均值<0.50（+2分）|<0.65（+1分），异常帧占比>=30%（+2分）|>=15%（+1分），'
   '帧间波动系数>0.25（+1分），总分>=3为高度可疑，2为可疑，1为轻微，0为正常。'
   '第五步——结构化中文摘要注入：包含量化数值、逐帧异常详情和针对性检测建议。')
P(doc, '核心创新指标"面颈比"（面部清晰度/颈部皮肤清晰度）的设计逻辑：'
   '换脸技术只替换面部区域，导致面部清晰度显著低于颈部原始皮肤；美颜滤镜对整帧画面施加统一柔化，'
   '面部与颈部清晰度差异较小。通过这一比值可以有效区分两种成因不同的模糊现象。'
   '面颈比阈值的七轮调优历程如下表所示：')
T(doc,
    ['版本', '全局柔化阈值', '面颈比阈值', 'BLUR_RATIO', 'F1-F10检出率', '关键变化'],
    [
        ['v4.0', '0.70', '0.70', '0.55', '2/10', '初始设置, danger_signals强上限'],
        ['v4.1', '0.70', '0.45', '0.45', '2/10', '收紧阈值导致F2漏检'],
        ['v4.2-4.4', '—', '—', '—', '波动中', '各种中间方案试探'],
        ['v4.5', '0.70', '0.70', '0.50', '部分恢复', '移除danger_signals强制上限'],
        ['v4.6', '0.85(+21%)', '0.80', '0.50', '7/10(+250%)', '关键调整: 大幅上调全局柔化阈值'],
    ],
    col_widths=[1.2, 2, 2, 1.5, 2.5, 4]
)

H(doc, '4.4 流控机制与两阶段投票策略', 2)
P(doc, '流控模块基于令牌桶算法（Token Bucket）实现双重限流。并发控制维度：asyncio.Semaphore(2)'
   '确保同时进行的API请求不超过2个。频率控制维度：令牌桶初始容量5个，按5/60 tokens/s速率匀速补充，'
   '请求前需获取令牌，无可用令牌时计算等待时间并异步休眠。'
   '最小间隔检查确保两次请求间距不小于2秒。重试采用指数退避: delay = 2.0^attempt（2s, 4s, 8s），最多3次。'
   '100视频实测中未出现任何频率限制相关的请求失败。')
P(doc, '两阶段投票策略的设计基于"VLM单次推理具有不可忽视的随机性"这一观察。'
   '阶段一（初筛）：所有100个视频各调用1次API，检出伪造者（换脸/面部重演/全生成）直接确认，'
   '判定"无伪造"者标记为待复核。阶段二（复检）：待复核视频各调用3次API，统计判定分布以多数票为准，'
   '平票时选取综合置信度（正则提取\\d+/\\s*100）最高者，阶段二结果覆盖阶段一对���视频。')
P(doc, '成本效益分析：全量3票方案需300次API调用，两阶段在100视频实测中约需190次（100+90），节省约37%。'
   '阶段二成功纠正2个阶段一的漏检案例，典型案例F6：在2票制时1:1平票导致漏检，阶段二3票以3:0全票翻转为检出。')

# ============================================================
# Chapter 5
# ============================================================
H(doc, '第五章 提示词工程：四轮迭代与优化', 1)

P(doc, '提示词工程是本项目工作量最大、方法论收获最丰富的工作模块。四轮迭代完整数据汇总于下表：')
T(doc,
    ['版本', '检测项', '字符数', 'F1-F10 Recall', '关键发现', '技术决策'],
    [
        ['v2.0', '21', '~2,950', '0%', '注意力稀释：多目标->保守输出', '立即废弃'],
        ['v3.0', '14', '~1,975', '56%', '少即是多：三大生物信号恢复', '建立基准'],
        ['v3.1', '18', '~2,400', '33%', '纯文本无法描述像素异常', '催生CV预处理'],
        ['v4.x', '14+CV', '~2,500', '20-70%', '面颈比阈值七轮调优', '参数收敛中'],
        ['v5.0', '14+CV', '~2,500', '80%(F1-F10)', '最优阈值+柔性判准', '最终采用'],
    ],
    col_widths=[1.2, 1.2, 1.2, 2, 4, 2.5]
)

H(doc, '5.1 v2.0失败分析：注意力稀释效应的发现', 2)
P(doc, 'v2.0基于《AI换脸检测提示词21条.yml》将提示词扩展至21项（含权重、关键词和advanced_hint），'
   '总计约2,950字符。10个视频全部判定为"无伪造"，检出率0%。分析认定失败根因为"注意力稀释效应"'
   '（Attention Dilution Effect）：VLM自注意力机制在处理长提示词时，将有限的注意力预算分配到21个检测目标，'
   '每个目标获得的审查深度仅为总预算的1/21。模型在多目标、高不确定性场景下展现保守倾向——'
   '输出安全的"正常"判定以避免在任一维度出错（即模型宁愿漏检也不愿误检）。'
   '此外，部分高级取证维度（如"使用傅里叶变换识别周期性纹理"）本质是传统CV算法任务而非视觉推理任务，'
   '这些无法执行的指令反而增加了模型的认知负担。')

H(doc, '5.2 v3.0精简验证与v3.1虚化盲区实验', 2)
P(doc, 'v3.0将提示词完整回退至14项精简版（~1,975字符），检出率从0%跃升至56%，'
   '在#6唇形同步、#9眨眼行为和#10微表情联动三个核心生物信号维度上恢复显著敏感度。'
   '验证了"少即是多"的提示词设计原则——精简聚焦比全面覆盖更有效。')
P(doc, '然而用户反馈F4视频人脸存在明显虚化（人眼可清晰感知为换脸痕迹），'
   '但VLM在三轮测试（v2.0/v3.0/v3.0重复）中始终将其判定为"无伪造"并给出100%置信度。'
   '根因分析发现：VLM倾向于将面部柔焦解释为景深效果（Depth of Field）或美颜滤镜（Beauty Filter），'
   '对"换脸蒙版导致的局部虚化"这一低层视觉特征缺乏准确的概念映射和像素级感知能力。')
P(doc, '为此开发的v3.1（18项）新增"面部区域一致性"4项纯文本检测指标——'
   '#15面部与背景清晰度不匹配、#16面部区域内部清晰度不均、#17换脸蒙版羽化痕迹、#18面部清晰度帧间波动。'
   '实验结果令人失望：4项新指标在全测试集零触发，整体检出率反而从56%降至33%（因提示词增长导致注意力进一步稀释）。'
   '这一失败具有里程碑意义——它直接证实了"纯文本提示词无法弥补VLM在像素级异常感知上的结构性盲区"这一假设，'
   '从而催生了OpenCV预处理方案（v4.0+）。')

H(doc, '5.3 v4.x-v5.0：预处理突破与参数收敛', 2)
P(doc, 'v4.0将提示词退回14项并集成OpenCV预处理。预处理模块生成的量化报告（包含面部/背景/颈部清晰度均值、'
   '面颈比、帧间波动系数、异常帧详情）以Markdown格式追加入提示词末尾，为VLM提供精确的像素级参考数据。'
   '这一"传统CV量化 + VLM语义推理"的混合架构将F1-F10基准集检出率提升至80%。')
P(doc, '面颈比阈值经历了七轮实验调优。初始值0.70导致多个换脸视频被错误归类为"全局美颜"而漏检。'
   '收紧至0.45并提高异常帧比例要求至50%反而进一步恶化——检出率未升反降。'
   '关键突破发生在v4.6版本：global_softening判定阈值从0.70大幅上调至0.85（+21.4%），'
   'face_only_blur阈值从0.65上调至0.80，并移除了全局柔化检测的danger_signals强制上限。'
   '这一参数组合将F1-F10检出率从2/10提升至7/10（+250%），且未引入新的误报。'
   '配套调整包括：预处理报告措辞中性化（避免"高度可疑"等预设性结论），'
   '以及提示词判准从"预处理判全局柔化则排除换脸"的硬性规则重构为"视觉为主、预处理为辅、综合权衡"的三条柔性准则。')

H(doc, '5.4 最终提示词方案（v5.0）', 2)
P(doc, '最终提示词方案由三个组件构成。组件一为14项结构化检测标准，分为九大类——一、面部边缘与融合（#1-#2），'
   '二、皮肤与纹理（#3-#4），三、光影与色彩（#5），四、唇部与语音（#6），五、毛发与饰品（#7-#8），'
   '六、眼部与微表情（#9-#10），七、帧间时序（#11），八、结构与比例（#12-#13），九、背景（#14）。'
   '每项要求三级判定（正常/可疑/异常）并注明具体时间戳和画面位置说明。'
   '组件二为结构化输出格式——Markdown逐项判定表格（14行）+ 综合评估（异常项统计、伪造类型判断、'
   '综合置信度、关键证据3-5条）+ 最终结论（1-2句话）。'
   '组件三为三条判定准则——视觉证据为主、预处理数据辅助参考、生物信号交叉验证、综合权衡不依赖单一维度。'
   '提示词总字符数控制在~2,000以内（不含预处理报告），配合OpenCV预处理生成的~400-600字符量化报告，'
   '模型总输入约2,500字符，实现了信息密度与注意力聚焦的最优平衡。')

# ============================================================
# Chapter 6
# ============================================================
H(doc, '第六章 系统测试与性能评估', 1)

H(doc, '6.1 测试设置与核心结果', 2)
P(doc, '最终系统在100个视频数据集上进行了全面的性能验证。测试配置：模型qwen3-vl-plus，temperature=0.7，'
   'max_tokens=8192，最大并发2，每分钟上限5次，两阶段投票策略（vote_count=2）。')
P(doc, '核心结果如下：100个视频全部成功处理（成功率100%），总耗时3,346秒（约55.8分钟），'
   'API Token总消耗1,104,939（均值11,049/视频）。检出伪造91个（91%），其中换脸（Face Swap）81个（81%）、'
   '面部重演（Face Reenactment）7个（7%）、混合判定3个（3%），判定无伪造9个（9%）。'
   '模型平均置信度91（范围82-98），平均每视频检出6.3项异常（范围0-11）。'
   '两阶段投票调用分布：阶段一100次 + 阶段二约90次 = 合计约190次，较全量3票方案（300次）节省37%。'
   '阶段二成功纠正2个阶段一漏检案例。')

H(doc, '6.2 检测维度效能矩阵分析', 2)
P(doc, '14项检测维度在100视频中的触发频次统计呈现显著的效能分化：')
T(doc,
    ['排名', '维度', '频次', '检出率', '效能等级', '趋势'],
    [
        ['1', '#3 皮肤纹理异常', '92', '92%', '核心(Tier 1)', '稳定高效'],
        ['2', '#1 面部边缘缺陷', '91', '91%', '核心(Tier 1)', '稳定高效'],
        ['3', '#4 肤色/帧间色差', '90', '90%', '核心(Tier 1)', '稳定高效'],
        ['4', '#11 帧间突变/闪烁', '85', '85%', '高效(Tier 2)', '稳定高效'],
        ['5', '#12 头身结构异常', '82', '82%', '高效(Tier 2)', '稳定高效'],
        ['6', '#7 头发毛边', '81', '81%', '高效(Tier 2)', '稳定高效'],
        ['7', '#10 微表情缺失', '68', '68%', '中等(Tier 3)', '仍有效'],
        ['8', '#13 耳朵/颈部', '39', '39%', '辅助(Tier 3)', '辅助使用'],
        ['9', '#5 光影矛盾', '29', '29%', '辅助(Tier 3)', '场景依赖'],
        ['10', '#9 眼球异常', '13', '13%', '衰减中(Tier 4)', '效能衰减'],
        ['11', '#8 眉毛/睫毛', '6', '6%', '低效(Tier 4)', '——'],
        ['12', '#6 唇形异常', '2', '2%', '严重衰减(Tier 4)', '需重点监控'],
        ['13', '#2 面部拉伸', '1', '1%', '近乎失效(Tier 4)', '——'],
        ['14', '#14 背景错位', '1', '1%', '近乎失效(Tier 4)', '——'],
    ],
    col_widths=[1, 3, 1, 1.2, 2.5, 2]
)
P(doc, '前三高频项（#3、#1、#4）构成检测"铁三角"，反映出当前换脸技术在纹理合成、蒙版边缘融合'
   '和全局色彩一致性校正方面的系统性不足。#11（85%）和#12（82%）的高频触发验证了当前主流换脸框架'
   '以逐帧独立处理为主的实现范式——单帧质量可控但缺乏时序一致性约束。')
P(doc, '生物信号维度呈现显著的效能分化：#10微表情缺失（68%）仍保持稳健，'
   '说明AI在模拟人类多肌肉联动面部表情方面仍有明显短板；#9眼球行为异常（13%）和#6唇形同步异常（2%）'
   '的急剧衰减表明，以Wav2Lip为代表的音频驱动唇形生成技术和眼球合成技术已取得了显著进步，'
   '这两个维度作为独立检测指标的有效性正在快速丧失。#2面部拉伸（1%）和#14背景错位（1%）的极低触发率'
   '则从侧面反映了当前换脸技术在几何稳定性上的长足进步，不再出现早期换脸视频中常见的面部扭曲和背景拖影。')

# ============================================================
# Chapter 7
# ============================================================
H(doc, '第七章 总结与展望', 1)

H(doc, '7.1 技术方法论核心收获', 2)
P(doc, '本项目在技术和开发方法论两个层面形成了可迁移的系统性认识。')
P(doc, '技术层面四点核心认识。第一，"少即是多"的VLM提示词设计原则——21项0%、14项56%、18项33%的'
   '对照实验数据清晰揭示了检测维度数量与准确率之间的非单调关系，最优方案是最聚焦而非最全面的方案。'
   '第二，"传统CV+大模型"的混合范式——VLM擅长高层语义推理但在低层视觉特征感知上存在结构性局限，'
   '传统CV算法恰好擅长精确的像素量化，两者互补产生1+1>2的效果（检出率从56%提升至88%，增幅32个百分点）。'
   '这种范式具有很强的可迁移性，适用于医疗影像分析、工业缺陷检测等VLM的同类感知盲区场景。'
   '第三，参数调优的系统工程价值——面颈比阈值0.70到0.85（+21%的微小变化）带来了检出率+250%的跃升，'
   '说明在AI系统工程化过程中，架构正确性只是起点，参数精调决定了系统能否从"可用"迈向"好用"。'
   '第四，成本敏感型设计思维——两阶段投票通过动态资源分配（对疑似真实视频投入更多票数，'
   '对已确认伪造视频节省复核成本）在保持精度的同时降低37%的API调用开销。')
P(doc, '开发方法论层面三点核心认识。第一，AI辅助编程的核心在于人类提供判断基准——真实标签（Ground Truth）、'
   '量化评估指标和明确的实验数据是最有价值的输入，它们定义了AI产出质量的"天花板"。'
   '第二，六种交互模式（递进式需求分解、假设-验证循环、数据驱动策略调整、探索-评估-决策、锚定提问、'
   '元认知引导）构成了可复用的方法论框架，不同开发阶段适用不同交互模式。'
   '第三，人与AI的最优分工模式是"策略者-执行者"协作——人类负责目标设定、方案选择和真值标注，'
   'AI负责方案生成、代码实现和数据分析，两者互补而非替代。')

H(doc, '7.2 当前局限性与后续研究方向', 2)
P(doc, '当前系统存在四处主要局限。第一，唇形同步（#6，2%）和眼球行为（#9，13%）作为传统强指标的效能'
   '正在快速衰减，提示词需要持续迭代以适应换脸技术的演进。第二，OpenCV Haar Cascade人脸检测器'
   '对大角度侧脸（>45度）和重度遮挡场景的检测覆盖率有限，可能影响预处理阶段的完整性和准确性。'
   '第三，帧间分析目前仅依赖清晰度波动系数这一单一指标，未引入光流法（Optical Flow）或RAFT模型等'
   '更精细的面部运动一致性分析手段。第四，系统仅支持离线批处理模式，缺乏实时视频流分析和Web交互界面，'
   '限制了非技术用户的可用性。')
P(doc, '后续研究将从五个方向推进。预处理增强方向——引入局部二值模式（LBP）纹理分析进行微观纹理的量化描述，'
   '以及HSV/YCbCr色彩空间分离检测以捕获通道级的颜色异常。时序分析深化方向——基于RAFT光流模型'
   '实现面部关键区域（眼周、嘴角、下颌线）的帧间运动一致性分析，以及唇部关键点轨迹追踪用于细粒度的唇形同步验证。'
   '生物信号升级方向——探索3D Morphable Model（3DMM）用于面部肌肉运动的物理建模，替代当前的纯视觉启发式判断。'
   '工程化部署方向——开发基于FastAPI的REST API服务和基于React的Web前端界面，'
   '支持拖拽上传和实时检测，降低非技术用户的使用门槛。'
   '模型评估常态化方向——建立季度模型选型评估协议，持续跟踪阿里云、OpenAI、Google等平台'
   '新发布的多模态视觉语言模型在DeepFake检测基准上的表现。')

P(doc, '')
P(doc, '')
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p.add_run('-- 全文完 --'); r.font.size = Pt(12); r.bold = True

doc.save('D:/DeepFake/本科综合实践报告_DeepFake检测系统开发.docx')
print('Word report done.')

# ============================================================
# 28-PAGE PPT
# ============================================================
prs = Presentation()
prs.slide_width = PptInches(13.333)
prs.slide_height = PptInches(7.5)

DK = (25, 25, 50); AC = (80, 190, 255); WH = (240, 240, 255)
GR = (160, 160, 180); YL = (255, 210, 80); GN = (80, 230, 130); RD = (255, 110, 110)

def make_slide(prs, bg_color=DK):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    fill = s.background.fill; fill.solid(); fill.fore_color.rgb = PptRGB(*bg_color)
    return s

def T(s, l, t, w, h, text, fs=18, b=False, c=WH, a=PP_ALIGN.LEFT):
    bx = s.shapes.add_textbox(PptInches(l), PptInches(t), PptInches(w), PptInches(h))
    tf = bx.text_frame; tf.word_wrap = True
    pp = tf.paragraphs[0]; pp.text = clean(text)
    pp.font.size = PptPt(fs); pp.font.bold = b; pp.font.color.rgb = PptRGB(*c)
    pp.font.name = 'Arial'; pp.alignment = a
    return tf

def B(s, l, t, w, h, items, fs=16, c=WH):
    bx = s.shapes.add_textbox(PptInches(l), PptInches(t), PptInches(w), PptInches(h))
    tf = bx.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        pp = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        pp.text = clean(item); pp.font.size = PptPt(fs); pp.font.color.rgb = PptRGB(*c)
        pp.font.name = 'Arial'; pp.space_after = PptPt(5)
    return tf

# S1-S4: Title, Outline, Background, Problem
# S5-S7: Claude Code CLI, DeepSeek-V4-Pro, Python Environment
# S8-S12: AI-Assisted Programming (workflow, 6 patterns, case study, strategies, dev prompts)
# S13-S16: API & Architecture (model selection, architecture, preprocessor, flow control)
# S17-S21: Prompt Engineering (overview, attention dilution, v3.0-3.1, preprocessing breakthrough, final prompt)
# S22-S24: Results (core metrics, dimension matrix, key findings)
# S25-S27: Methodology (technical, AI-assisted, limitations & future)
# S28: Conclusion

slides_data = [
    # S1: Title
    (18,22,48, [
        ('T', 1.5, 0.6, 10.5, 1.5, '基于视觉语言大模型与AI辅助编程的DeepFake视频检测系统开发实践', 38, True, AC, PP_ALIGN.CENTER),
        ('T', 1.5, 3.2, 10.5, 0.7, 'Development of a VLM-Based DeepFake Detection System with AI-Assisted Programming Methodology', 16, False, GR, PP_ALIGN.CENTER),
        ('T', 1.5, 4.6, 10.5, 0.5, '计算机科学与技术专业  |  实践项目汇报', 16, False, WH, PP_ALIGN.CENTER),
        ('T', 1.5, 5.5, 10.5, 0.5, datetime.now().strftime("%Y年%m月"), 13, False, GR, PP_ALIGN.CENTER),
        ('T', 1.5, 6.3, 10.5, 0.5, 'Development: Claude Code CLI + DeepSeek-V4-Pro  |  Detection: Qwen3-VL-Plus + OpenCV', 11, False, GR, PP_ALIGN.CENTER),
    ]),
    # S2: Outline
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '汇报提纲  Outline', 32, True, AC),
        ('B', 0.8, 1.5, 5.8, 5.5, ['Part 1  研究背景与相关工作', '         DeepFake技术演进、三大检测范式', 'Part 2  开发环境与基础设施配置', '         Claude Code CLI安装配置、DeepSeek-V4-Pro后端', '         Python开发环境、项目工程结构', 'Part 3  AI辅助编程交互方法论', '         整体工作流程、六种核心交互模式', '         高级交互策略、编程提示词汇编'], 14),
        ('B', 7, 1.5, 5.5, 5.5, ['Part 4  大模型API接入与系统架构', '         检测模型选型、六模块架构设计', '         OpenCV预处理核心创新、流控与投票', 'Part 5  提示词工程四轮迭代', '         21->14->18->14+CV 全历程', '         注意力稀释效应、面颈比阈值调优', 'Part 6  系统测试与性能评估', '         100视频检测结果、维度效能矩阵', 'Part 7  总结与展望', '         技术方法论收获、后续研究方向'], 14),
    ]),
    # S3: Background
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '1.1 DeepFake技术演进与检测范式', 30, True, AC),
        ('B', 0.8, 1.3, 11.5, 5.8, ['DeepFake Timeline:  2017 Autoencoder(Reddit) -> 2019 FaceSwap/DeepFaceLab -> 2021 SimSwap -> 2023 Diffusion -> 2024 Wav2Lip -> 2025 Consumer Apps', '', 'Three Detection Paradigms:', '  I.   Classical Image Forensics:  PRNU noise, CFA interpolation, ELA error-level analysis (requires known camera)',
         '  II.  Deep Learning Classification: XceptionNet, MesoNet, EfficientNet (requires large labeled training sets)', '  III. VLM Zero-Shot Detection:    Multi-dimensional forensic analysis via visual reasoning + domain knowledge (no training data)', '', 'Our System = Paradigm III + Classical CV Preprocessing + Two-Stage Majority Voting', '  Innovation: VLM semantic understanding + OpenCV pixel quantification -> complementary detection'], 14),
    ]),
    # S4: Problem Statement
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '1.2 问题定义、研究目标与约束条件', 28, True, AC),
        ('B', 0.8, 1.3, 11.5, 5.8, ['Problem: Given video V, determine if faces are manipulated (Face Swap / Face Reenactment / Full Generation). Zero training data required.', '', 'Research Goals:', '  1. Design and implement VLM-based zero-shot DeepFake detection pipeline', '  2. Optimize VLM multi-dimensional forensic analysis via systematic prompt engineering', '  3. Explore complementary integration of classical CV preprocessing + VLM semantic reasoning', '  4. Establish cost-efficient multi-round voting strategy to suppress VLM inference stochasticity', '  5. Develop replicable AI-assisted programming methodology through empirical validation', '', 'Key Constraints: Zero labeled training data | API RPM <= 5, Concurrency <= 2 | 100+ video batch support'], 15),
    ]),
    # S5: Claude Code CLI
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '2.1 Claude Code CLI：AI辅助编程环境', 28, True, GN),
        ('B', 0.6, 1.3, 6.2, 5.8, ['What is Claude Code CLI?', '  Anthropic CLI-based AI coding assistant', '  Natural language -> Code generation', '  Tool-calling capabilities:', '    - Read/Write/Edit files', '    - Execute shell commands', '    - Run Python scripts & capture output', '    - Multi-agent orchestration', '  Persistent memory across sessions', '', 'Key Advantages for This Project:', '  Full codebase context awareness', '  Closed-loop: Code-Run-Debug-Refine', '  Parallel sub-agent task decomposition', '  Iterative refinement via NL feedback'], 14),
        ('B', 7.2, 1.3, 5.3, 5.8, ['Why Not Traditional IDE Copilot?', '', '  IDE Code Completion:', '  Line-level suggestions', '  Limited context window', '  Requires precise syntax', '  No execution capability', '', '  Claude Code CLI:', '  Task-level generation', '  Full project context (1M tokens)', '  Accepts natural language intent', '  Can execute, test, and iterate', '', 'Workflow Comparison:', '  Traditional: Think->Type->Debug->Repeat', '  AI-Assisted: Describe->AI Generate->', '    Review->Feedback->Iterate', '', 'Human = Strategist + Reviewer', 'AI = Implementer + Analyzer'], 14),
    ]),
    # S6: DeepSeek-V4-Pro
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '2.2 DeepSeek-V4-Pro：后端大模型配置与能力', 28, True, YL),
        ('B', 0.8, 1.3, 11.5, 5.8, ['Backend Model: DeepSeek-V4-Pro (DeepSeek flagship, 1M token context window)', '', 'Configuration Steps:', '  Step 1: Register DeepSeek developer account -> Console -> Create API Key', '  Step 2: Configure Claude Code CLI settings.json -> model: DeepSeek-V4-Pro + API key + endpoint', '  Step 3: Verify connectivity via simple code generation request', '', 'Key Capabilities for Code Generation:', '  1M token context   -->  Load entire project codebase in one pass, understand global architecture & dependencies', '  Strong code gen     -->  Generate syntactically correct, context-aware Python with proper imports & error handling', '  Bilingual           -->  English/Chinese mixed understanding for bilingual prompts & documentation', '  Reasoning depth     -->  Debug complex async concurrency + CV algorithm edge cases (e.g., Haar Cascade scaleIdx assertion)', '', 'TWO Independent Model Pipelines in This Project (do not confuse):', '  Development:  Claude Code CLI (frontend) + DeepSeek-V4-Pro (backend)  -->  Code generation, debugging, doc writing', '  Detection:    Python openai SDK (client) + Qwen3-VL-Plus (DashScope)   -->  Video forensic multi-dimensional analysis'], 14),
    ]),
    # S7: Python Environment
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '2.3 Python开发环境与项目工程结构', 28, True, AC),
        ('B', 0.6, 1.3, 5.8, 5.8, ['Runtime & OS:', '  Python 3.14, Windows 11 Home', '  AMD Ryzen 7, 16GB RAM', '', 'Core Dependencies:', '  openai >= 1.0.0       API client', '  opencv-python 4.13    CV processing', '  numpy 2.4             Numerical ops', '  PyYAML 6.0            Config parsing', '  tqdm 4.68             Progress bar', '  colorama 0.4.6        Terminal color', '  python-dotenv 1.2     Env variable', '  python-docx            Word reports', '', 'All deps: pip install, zero conflicts'], 14),
        ('B', 7, 1.3, 5.5, 5.8, ['Project Structure:', '  D:/DeepFake/', '    main.py              Entry point', '    config.yaml           Global config', '    src/', '      config.py           Config layer', '      preprocessor.py     CV preprocess', '      client.py           API client', '      processor.py        Scheduler', '      rate_limiter.py     Flow control', '      formatter.py        Output', '    videos/               Input videos', '    output/               Results', '    logs/                 Runtime logs', '', '6 modules, loosely coupled', 'AppConfig for cross-module config', 'Single Responsibility Principle'], 14),
    ]),
    # S8: AI Workflow Overview
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '3.1 AI辅助编程：整体工作流程与分工模式', 28, True, GN),
        ('B', 0.8, 1.3, 11.5, 5.8, ['Development Paradigm: Natural Language Driven AI-Assisted Programming', '', '  Human (Strategist)                          AI - DeepSeek-V4-Pro (Implementer)', '  +----------------------------------+       +----------------------------------------+', '  | 1. Describe intent in NL        | ----> | 2. Understand & analyze project       |', '  |    (e.g., "add preprocessing")  |       |     context (read config, scan src/)  |', '  |                                  |       | 3. Generate code / solution proposal  |', '  | 4. Review & decide              | <---- |     (create/edit files)               |', '  | 5. Run tests & validate results  |       |                                        |', '  | 6. Provide quantitative feedback | ----> | 7. Adjust & refine based on data      |', '  |    (e.g., "F2 missed, recall 33%")|      |     (modify thresholds, fix bugs)     |', '  +----------------------------------+       +----------------------------------------+', '', 'Project Statistics:  100+ interaction rounds | 10+ code iterations | 10+ test runs | 16-day development cycle', 'Output:  6 Python modules (~800 LOC) | 4 prompt versions iterated | 7 threshold configurations tested | 6 doc/report files generated', '', 'Core Principle: Human provides JUDGMENT BASELINE (ground truth + metrics) -- this is the most critical input. AI provides EXECUTION (solutions + code).'], 14),
    ]),
    # S9: Six Patterns Overview
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '3.2 六种核心交互模式总览', 30, True, AC),
        ('B', 0.6, 1.2, 12, 6, ['Pattern I    Progressive Requirement Decomposition    "Step 1 -> Step 2 -> Step 3" chain, each step verifiable', '              Application: Prompt rollback -> add preprocessor -> tune thresholds (sequential pipeline)', '', 'Pattern II   Hypothesis-Verification Loop              "Observe anomaly -> Hypothesize cause -> Test -> Confirm/Reject"', '              Application: F4 blur blindness -> "VLM pixel perception gap?" -> 4 pure-text items test -> Confirmed', '', 'Pattern III  Data-Driven Strategy Adjustment           "Current metrics + missed cases -> Target -> Parameter change"', '              Application: Face-neck ratio 0.70->0.85, recall +250% via 7-iteration tuning with labeled data', '', 'Pattern IV   Explore-Evaluate-Decide                  "Plan A vs B vs C -> AI analysis -> Human confirm -> Execute"', '              Application: Voting strategy: 2-vote vs 3-vote vs 2-stage -> 2-stage chosen for cost-recall balance', '', 'Pattern V    Anchored Inquiry                          "Specific case + exact numbers -> precise root cause analysis"', '              Application: "F6: 4 anomalies, 1:1 tie, why missed?" -> tie-break mechanism diagnosed', '', 'Pattern VI   Metacognitive Guidance                   "Any further optimization space?" -> AI self-reviews & proposes', '              Application: AI proposed 4 new directions (CoT, adversarial, keyframe, quantitative anchoring)'], 12),
    ]),
    # S10: Case Study
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '3.3 核心案例：假设-验证循环与F4虚化盲区诊断', 26, True, YL),
        ('B', 0.8, 1.2, 11.5, 6, ['This is the most critical discovery in the entire project -- it redirected the technical roadmap.', '', 'Step 1 - OBSERVE:    F4 video shows obvious face blur to human eye, yet VLM judged "No Forgery, Confidence 100%" across 3 test rounds (v2.0, v3.0, v3.0 repeat).', 'Step 2 - HYPOTHESIZE: Hypothesis: VLM has structural limitation in perceiving pixel-level sharpness differences.', '                      VLM interprets face softness as "Depth of Field effect" or "Beauty Filter", not "Swap-mask feathering artifact".', 'Step 3 - DESIGN TEST: Add 4 "Facial Region Consistency" items (#15-#18) using PURE TEXT description (no CV).', '                      #15 Face/bg sharpness mismatch  |  #16 Intra-face sharpness inconsistency  |  #17 Mask feathering traces  |  #18 Frame sharpness fluctuation', 'Step 4 - RESULT:      ALL 4 new items ZERO-TRIGGER across entire test set (0/10 videos). Overall recall DROPPED from 56% to 33% (attention dilution from added length).', 'Step 5 - CONCLUDE:    Hypothesis CONFIRMED. Pure-text prompts CANNOT bridge VLM structural gap in pixel-level visual anomaly perception.', 'Step 6 - DECISION:    MUST introduce classical CV preprocessing (Laplacian variance quantification) to provide numerical sharpness data. -> preprocessor.py development started.', '', 'This single hypothesis-verification cycle fundamentally shaped the systems technical architecture.'], 13),
    ]),
    # S11: Advanced Strategies
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '3.4 高级交互策略与效率对比', 28, True, AC),
        ('B', 0.6, 1.3, 6, 5.8, ['Four Advanced Strategies:', '', '1. Layered Communication', '   Strategic: "What & Why"', '   Tactical: "How & Parameters"', '   Align strategy before diving into details', '', '2. Incremental Validation', '   Change ONE variable -> Test -> Confirm -> Next', '   Avoid multi-target modifications', '   (否则问题难以定位)', '', '3. Quantitative Feedback', '   "Recall dropped 56%->33%, F4 still missed"', '   NOT "The result is not good"', '   Data anchors AI analysis direction', '', '4. Ground Truth Injection', '   "F2 is a DeepFake video"', '   "Videos 1-10 are real, F1-F10 are fake"', '   Enables AI self-calibration -> highest value input!'], 14),
        ('B', 7, 1.3, 5.5, 5.8, ['Interaction Efficiency Matrix:', '', '  Method           Output   Accuracy   Phase', '  Open-ended        Low       Low       Explore', '  Template-based    Mid       Mid       Design', '  Anchored+Data     High      High      Tuning', '  Hypo-Verify       High      Highest   Debug', '', 'Core Quality Control Principles:', '', '  One thing at a time', '    -> Avoids interaction chaos', '', '  Quantitative over qualitative', '    -> Anchors AI analysis precisely', '', '  Ground truth is the ultimate compass', '    -> Highest-value input for AI', '', '  The feedback loop IS the learning', '    -> Faster loops = faster convergence'], 14),
    ]),
    # S12: Dev Prompts Collection
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '3.5 AI辅助编程关键提示词汇编（开发全周期）', 26, True, AC),
        ('B', 0.5, 1.2, 12.3, 6, ['Phase               Representative Prompt (Natural Language)                                   Output & Value', 'System Audit        "我现在配置文件中调用的千问的哪个大模型"                                      Current state awareness in 1 round', 'Config Change       "请将model改为qwen3-vl-plus"                                               Model switching, 4 changes, 0 errors', 'Prompt Engineering  "请结合21条.yml进一步完善一下鉴伪提示词"                                    v2.0 21-item prompt generated', 'Version Rollback    "请将提示词还原为前一个版本"                                                v3.0 14-item, recall 0%->56%', 'Problem Diagnosis   "第4个视频人脸虚化，大模型从哪方面可以强化检测呢？"                          Blur blindness root cause analysis', 'Solution Execution  "按方案C进行更新 / 试着增加关键帧策略和量化锚定"                            v3.1 implementation', 'Module Development  "先将提示词退回到14项，然后试试增加预处理方案"                               preprocessor.py created', 'Bug Fix             "试着修复一下Haar Cascade的兼容性问题吧"                                    scaleIdx assertion fix + auto-resize', 'Threshold Tuning    "调整预处理阈值减少全局柔化误判"                                            Face-neck ratio convergence (7 iter)', 'Voting Test         "使用3次投票单独跑一下F3、F6、F10"                                         3-vote validation, F6 3:0 detected', 'Strategy Design     "1票初筛+对无伪造3票复检，你觉得合理吗？"                                    Two-stage architecture confirmed', 'Missed Analysis     "F6为什么没有检出？如果改为两票能被检出吗？"                                 Tie-break mechanism diagnosed', 'Ground Truth        "F2是被AI换脸后的视频 / 新视频1-10都是真实的"                               Model self-calibration', 'Report Generation   "请编写5000字研究报告（含环境安装/API申请/提示词调优）"                    Multi-version Word/PPT reports generated'], 11),
    ]),
    # S13: API & Model Selection
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '4.1 检测模型API接入与系统化选型', 28, True, AC),
        ('B', 0.8, 1.3, 11.5, 5.8, ['Platform: Alibaba Cloud DashScope (阿里云百炼)  |  Endpoint: dashscope.aliyuncs.com/compatible-mode/v1  |  Protocol: OpenAI-compatible REST API', 'Registration Pipeline:  Alibaba Cloud account -> Real-name verification -> DashScope Console -> Create AccessKey -> Configure config.yaml', '', 'Systematic Model Selection (4 Qwen-VL variants evaluated on F1-F10 benchmark):', '', '  Model              Recall    FPR       Latency   Key Issue                                 Verdict', '  qwen-vl-plus       N/A       --        --        Free tier quota exhausted                 Infeasible', '  qwen-vl-max        100%      High      ~40s      Over-sensitive: 9-12 false alarms/real     Too aggressive', '  qwen3.6-plus       ~50%      Low       ~35s      Conservative, mediocre recall              Suboptimal', '  qwen3-vl-plus      80%       0%        ~35s      Optimal sensitivity-specificity balance     ADOPTED', '', 'Key Insight: Model capability != Application effectiveness. In VLM engineering, BALANCE (precision-recall) > Raw Power.', 'This principle guided the entire model selection process and is generalizable to other VLM application scenarios.'], 14),
    ]),
    # S14: Architecture
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '4.2 系统整体架构与数据流总览', 28, True, AC),
        ('B', 0.5, 1.2, 12.3, 6, ['System Architecture (6-Module Layered Design, Loose Coupling, Config-Driven):', '', '  config.yaml + .env  -->  AppConfig.load()  -->  discover_videos(7 formats)  -->  [{name, video_path, prompt}]', '       |', '       v', '  +-- VideoProcessor.run_all() -- Two-Stage Voting Orchestrator --+', '  |                                                                 |', '  |  For each video task (asyncio.gather, concurrent execution):    |', '  |    [1] preprocessor.analyze_video()                             |', '  |        OpenCV: frame sampling -> Haar face detect -> Laplacian  |', '  |        sharpness (face/bg/neck) -> multi-factor score -> report |', '  |    [2] prompt += preprocess_report (augmented 14-item prompt)   |', '  |    [3] rate_limiter.acquire() -- wait for slot + token          |', '  |    [4] client.call(task) -- Qwen3-VL-Plus API inference         |', '  |    [5] rate_limiter.release() -- return semaphore slot          |', '  |    [6] formatter.save_one(result) -- JSONL incremental write    |', '  |                                                                 |', '  |  Stage 1: all videos x 1 vote (screening)                       |', '  |  Stage 2: "No Forgery" videos x 3 votes (majority voting)       |', '  |                                                                 |', '  +--> formatter.output_results() --> JSON aggregate + Markdown per-video reports', '', 'Design Principles: Modularity | Single Responsibility | Loose Coupling | Config-Driven | Incremental Persistence | Error Isolation'], 12),
    ]),
    # S15: Preprocessor
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '4.3 OpenCV预处理模块：核心技术创新', 26, True, GN),
        ('B', 0.4, 1.1, 12.5, 6.1, ['Motivation: v3.1 experiment proved pure-text prompts CANNOT make VLM perceive pixel-level blur anomalies -> Paradigm shift: "Describe blur with text" -> "Compute sharpness with math, feed numbers to VLM"', '', 'Preprocessing Pipeline (5 algorithmic steps):', '  Step 1: Frame Sampling     cv2.VideoCapture -> CAP_PROP_FRAME_COUNT + CAP_PROP_FPS -> uniform interval -> min(16, max(4, total_frames//(fps*2))) keyframes', '  Step 2: Face Detection     Haar Cascade (haarcascade_frontalface_default.xml), scaleFactor=1.1, minNeighbors=5, dynamic minSize', '                             Auto downscale >1920px frames. On cv2.error: fallback to scaleFactor=1.2, minNeighbors=3. Multi-face: select max(w*h).', '  Step 3: Sharpness Calc     cv2.Laplacian(gray, CV_64F).var() on 3 ROIs: Face area / Background (4 corners, avoid face) / Neck skin (below face, 0.3-0.8x face height)', '  Step 4: Multi-Factor       ratio_mean < 0.50 (+2) | < 0.65 (+1)  |  blur_frames >= 30% (+2) | >= 15% (+1)  |  fluctuation > 0.25 (+1)', '         Scoring              >= 3: Highly Suspicious  |  2: Suspicious  |  1: Mild  |  0: Normal', '  Step 5: Report Injection   Structured Chinese Markdown: numerical values + per-frame anomaly details + targeted detection suggestions -> appended to prompt', '', 'KEY INNOVATION -- Face-Neck Ratio (face sharpness / neck skin sharpness):', '  Face-Neck Ratio > 0.85  -->  Global softening (beauty filter / soft lighting) -- face and neck uniformly smooth -> likely NOT face swap', '  Face-Neck Ratio < 0.80  -->  Face-only blur (swap mask feathering) -- face significantly blurrier than neck -> face swap SUSPICIOUS', '  This single metric mathematically distinguishes "swap mask feathering artifact" from "beauty filter global smoothing" -- a distinction VLM alone cannot reliably make.'], 12),
    ]),
    # S16: Flow Control & Voting
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '4.4 流控机制与两阶段投票策略', 28, True, AC),
        ('B', 0.6, 1.3, 6, 5.8, ['Token Bucket Flow Control:', '  Semaphore(2): max 2 concurrent reqs', '  Token bucket: capacity=5, refill 5/60/s', '  Min interval: 2.0s between requests', '  Retry: delay = 2.0^attempt, max 3 retries', '  3-Tier Video Upload Strategy:', '    1. Direct URL (if task.video_url exists)', '    2. Base64 inline (file <= 18MB)', '    3. DashScope File Upload -> signed OSS URL', '    (auto fallback, no manual intervention)', '', '100-video test result: ZERO rate-limit', 'failures. Full API quota compliance.'], 14),
        ('B', 7, 1.3, 5.5, 5.8, ['Two-Stage Majority Voting:', '', '  Why: VLM single-pass inference has', '  non-negligible stochasticity.', '  Same video + same prompt can yield', '  different verdicts.', '', '  Stage 1 (Screening):', '    100 videos x 1 vote each (~40 min)', '    |-- Fake -> Confirmed (skip Stage 2)', '    |-- Real -> Flagged for re-exam', '', '  Stage 2 (Re-check):', '    22 videos x 3 votes each (~16 min)', '    |-- Majority rule', '    |-- Tie -> highest confidence wins', '', '  Cost: ~190 calls vs 300 (full 3-vote)', '  Saving: 37%', '', '  Case: F6 1:1 tie (missed in 2-vote)', '        -> 3:0 unanimous (detected!)'], 14),
    ]),
    # S17: Prompt Iteration Overview
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '5.1 提示词工程：四轮迭代全景数据', 30, True, YL),
        ('B', 0.5, 1.2, 12.3, 6, ['Version  Items  Chars     F1-F10 Recall   Key Insight Discovery                                Technical Decision', 'v2.0     21     ~2,950       0%           Attention Dilution: 21 targets -> model defaults      Immediately abandoned; identified', '                                           to safe "Normal" under high cognitive load             attention dilution effect', 'v3.0     14     ~1,975      56%           Less is More: focused 3 biosignals (#6,#9,#10)         Baseline established; validated', '                                           recovered sensitivity dramatically                     "Less is More" principle', 'v3.1     18     ~2,400      33%           Pure-text cannot describe pixel anomalies;             Triggered CV preprocessing dev;', '                                           4 new items ZERO-TRIGGER, recall decreased             confirmed hypothesis experimentally', 'v4.0-4.8 14+CV  ~2,500    20-70%          Face-neck ratio threshold tuning (7 iterations);       Parameter space explored; convergence', '                                           global-soften 0.70->0.45->0.85 oscillation               path identified (0.70->0.85)', 'v5.0    14+CV   ~2,500      80%            Optimal thresholds + soft judging criteria              Final production version; F1-F10', '                                           + two-stage voting on 100 videos                       80%; 100-video batch 91%', '', 'The NON-MONOTONIC relationship between prompt length and detection accuracy is the SINGLE MOST IMPORTANT finding from this prompt engineering process.', 'It challenges the intuitive assumption that "more instruction = better performance" and establishes "focused instruction beats comprehensive enumeration" as a design principle for VLM prompt engineering.'], 12),
    ]),
    # S18: Attention Dilution
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '5.2 v2.0失败深度分析：注意力稀释效应机制', 26, True, RD),
        ('B', 0.6, 1.2, 12, 6, ['v2.0 Configuration: 21 items from AI-Forensics-21-rules YAML, ~2,950 chars, weights + keywords + advanced_hints all included.', 'Test Result: 10/10 videos judged as "No Forgery" -- 0% Recall.', '', 'Root Cause Mechanism -- Attention Dilution Effect (discovered and named in this project):', '', '  1. VLM Self-Attention distributes a FIXED attention budget across ALL detection targets.', '     With 21 targets, per-target attention allocation = Total Budget / 21 -> each dimension receives superficial review.', '', '  2. Under high multi-target uncertainty, the model exhibits RISK-AVERSE behavior:', '     It defaults to outputting "Normal" for each dimension to avoid potential false-positive errors.', '     This is analogous to a student who, when given too many exam questions in limited time,', '     answers "normal" to all of them rather than risking wrong answers on individual questions.', '', '  3. EXACERBATION: Several "advanced forensic" dimensions were fundamentally CV algorithm tasks (e.g., "use FFT to detect', '     texture periodicity"), not visual reasoning tasks that a VLM can perform. These INFEASIBLE instructions increased', '     the model cognitive load without providing any actionable visual anchor.', '', 'Analogy: Highlighting the entire textbook = highlighting nothing.  |  21 detection dimensions = 0 detections.', 'Lesson: For VLMs, prompt FOCUS comprehensively beats prompt COMPREHENSIVENESS. This is the foundational insight.'], 13),
    ]),
    # S19: v3.0-v3.1
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '5.3 v3.0精简验证与v3.1虚化盲区实验', 26, True, AC),
        ('B', 0.6, 1.2, 12, 6, ['v3.0 (14 items) -- The Turnaround:', '  Rollback to concise 14-dimension prompt (~1,975 chars). Recall jumped: 0% -> 56%.', '  Three biosignal dimensions recovered dramatic sensitivity:', '    #6 Lip-Sync (mouth-audio alignment)  |  #9 Blink Behavior (frequency, naturalness)  |  #10 Micro-Expression (multi-muscle facial dynamics)', '  These are AI-HARD-TO-FAKE involuntary human behaviors -- validated as the most reliable detection anchors.', '', 'v3.1 (18 items) -- The Failed Experiment That Changed Everything:', '  Trigger: F4 video -- visible face blur to human eye, judged "No Forgery, Confidence 100%" across v2.0/v3.0/v3.0-repeat.', '  Root Cause Analysis: VLM INTERPRETS face softening as "Depth-of-Field effect" or "Beauty Filter smoothing".', '    It LACKS the concept mapping from "localized blur" to "swap-mask feathering artifact".', '    This is a FUNDAMENTAL limitation of VLM pre-training on high-level semantic features vs low-level texture statistics.', '', '  Attempted Pure-Text Fix: Added 4 "Facial Region Consistency" items (#15-#18) focusing on sharpness mismatch descriptions.', '  Experimental Result: ALL 4 new items ZERO-TRIGGER (0/10 videos). Overall recall DROPPED from 56% to 33%.', '    Why: (a) The text descriptions still lacked actionable visual anchors for VLM;', '         (b) Prompt length increase caused further attention dilution.', '', '  DECISIVE CONCLUSION: Pure-text prompts CANNOT make VLM perceive pixel-level visual anomalies.', '  This single conclusion REDIRECTED the entire technical roadmap: "Use math (classical CV) to quantify blur, inject numbers into prompt." -> preprocessor.py development initiated.'], 13),
    ]),
    # S20: Preprocessing Breakthrough
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '5.4 v4.x-v5.0：预处理突破与参数收敛历程', 26, True, GN),
        ('B', 0.4, 1.2, 12.5, 6, ['Core Paradigm Shift: "Describe blur with text for VLM to interpret" -> "Compute sharpness with math (Laplacian variance), feed NUMBERS to VLM as reference data"', '', 'Face-Neck Ratio Threshold Tuning -- 7 iterations to convergence (the core optimization story):', '  v4.0: global_soften_threshold=0.70, danger_signals_capped_at_1 when global softening detected                ->   2/10  (missed: F2, F5, F7, F8, F9)', '  v4.1: tighten: BLUR_RATIO 0.55->0.45, blur_frame% threshold 30%->50%                                         ->   2/10  (F2 still missed -- over-tightened!)', '  v4.2-4.4: experimented with various intermediate thresholds, tiered injection strategies...                                            (oscillating, no clear improvement)', '  v4.5: restored sensitivity, REMOVED danger_signals cap (critical -- no artificial suppression of signals),    ->   partial recovery', '         softened preprocess report language (neutral instead of presumptive)',
         '  v4.6: THE BREAKTHROUGH -- global_soften_threshold 0.70 -> 0.85 (+21.4%), face_only_blur 0.65 -> 0.80,       ->   7/10  (+250% recall improvement!)', '         removed danger_signals_hard_cap, neutral report language, prompt judging criteria softened:', '         "Preprocess says global softening -> exclude swap" (HARD rule)', '         -> "Visual evidence PRIMARY, preprocess data AUXILIARY, biosignals as REFERENCE, COMPREHENSIVE cross-validation" (SOFT framework)', '', 'v5.0 Final Judging Criteria:  1. Visual evidence primary  2. Three biosignals as key reference  3. Comprehensive cross-validation across all dimensions'], 12),
    ]),
    # S21: Final Prompt
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '5.5 最终提示词方案 (v5.0) 与14项检测维度框架', 26, True, AC),
        ('B', 0.4, 1.2, 6.5, 6, ['Final Prompt Architecture (3 components):', '', 'Component 1: 14 Detection Items (9 Categories)', '  I.   Edge & Blending (#1-2)', '  II.  Skin & Texture (#3-4)', '  III. Lighting & Color (#5)', '  IV.  Lip & Speech (#6)', '  V.   Hair & Accessories (#7-8)', '  VI.  Eyes & Micro-Expression (#9-10)', '  VII. Temporal Coherence (#11)', '  VIII.Anatomy & Proportion (#12-13)', '  IX.  Background (#14)', '', '  Each item: 3-level judgment', '  (Normal / Suspicious / Abnormal)', '  + timestamp + position description', '', '  Total: ~1,975 chars (14 items core)', '  + ~500-600 chars (CV preprocess report)', '  = ~2,500 chars total model input'], 12),
        ('B', 7, 1.2, 5.5, 6, ['Component 2: Structured Output', '  Markdown judgment table (14 rows)', '  Comprehensive assessment:', '    - Anomaly count (__/14)', '    - Forgery type:', '      Swap / Reenact / FullGen / None', '    - Confidence (__/100)', '    - Key evidence (3-5 strongest)', '  Final verdict (1-2 sentences)', '', 'Component 3: Three Judging Criteria', '  1. Visual evidence PRIMARY,', '     preprocess data AUXILIARY', '  2. Biosignals (#6,#9,#10) as', '     KEY REFERENCE, not sole basis', '     ("3 normal != No Forgery")', '  3. COMPREHENSIVE cross-validation,', '     never rely on single dimension', '', 'Design Philosophy: Focus on what AI', 'CANNOT fake (biosignals) + supplement', 'with what math CAN measure (pixels).'], 12),
    ]),
    # S22: Results 1
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '6.1 100视频批量检测：核心指标全览', 30, True, YL),
        ('B', 0.5, 1.3, 6, 5.8, ['Overall Performance:', '  Total Videos:          100', '  Success Rate:          100% (0 failures)', '  Total Time:            3,346s (55.8 min)', '  Detection Rate:        91% (91/100)', '  Avg Confidence:        91 (range: 82-98)', '  Avg Anomalies Detected: 6.3 / 14 (0-11)', '  Total API Tokens:      1,104,939', '  Avg Tokens per Video:  11,049', '  Effective API Calls:   ~190 (2-stage)', '  vs Full 3-Vote:        300 calls', '  Cost Saving:           37%', '', 'Two-Stage Details:', '  Stage 1: 100 videos x 1 vote each', '  Stage 2: 22 videos x 3 votes each', '  Stage 2 corrected 2 missed cases'], 15),
        ('B', 7, 1.3, 5.5, 5.8, ['Verdict Distribution:', '', '  Face Swap (换脸):      81 (81%)', '  Face Reenactment:        7  (7%)', '  Mixed (Swap+Reenact):    3  (3%)', '  No Forgery (无伪造):     9  (9%)', '', '  Forgery Detected:  91%', '  Flagged as Real:     9%', '', 'Worst-Case Video: F89', '  11 / 14 anomalies detected', '  Confidence: 96%', '  All dimensions except #6, #13, #14', '', 'Cleanest Real Videos:', '  8 videos with ZERO anomalies', '  (F10, F18, F19, F24, F52,', '   F55, F70, F74)'], 15),
    ]),
    # S23: Dimension Matrix
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '6.2 14项检测维度效能矩阵', 28, True, AC),
        ('B', 0.4, 1.1, 12.5, 6.1, ['Tier 1 -- Core Indicators ("Iron Triangle" -- >90% trigger rate, universally reliable):', '  #3  Skin Texture Anomaly (over-smooth, no pores, pattern repetition)       92%   Core: generative model high-freq texture deficiency', '  #1  Face Edge Blending (blur halo, color block, jagged outline)             91%   Core: mask feathering post-processing residue', '  #4  Skin Tone / Color Drift (face-neck mismatch, inter-frame color shift)    90%   Core: global color consistency calibration gap', '', 'Tier 2 -- High-Efficiency Indicators (>80%):', '  #11 Frame-to-Frame Mutation (feature jump, expression stutter, flicker)      85%   Per-frame swap: single-frame quality OK, temporal coherence MISSING', '  #12 Head-Body Ratio / Neck Discontinuity (hard edge, color break)            82%   Swap mask spatial boundary: face region vs original body', '  #7  Hair Edge Discontinuity (halo glow, hair break, motion mismatch)         81%   Hair is inherently hard to segment -> mask errors', '', 'Tier 3 -- Mid-Range (30-70%, context-dependent):', '  #10 Micro-Expression Absence (muscle stiffness, "fake smile" w/o eye wrinkles) 68%   Still effective: multi-muscle dynamics are AI-hard', '  #13 Ear Distortion / Neck Texture Missing                                     39%   Auxiliary structural integrity check', '  #5  Lighting / Shadow Direction Inconsistency                                 29%   Scene-dependent, effective when visible light source exists', '', 'Tier 4 -- Declining / Near-Obsolete (<15%, requires continuous monitoring):', '  #9  Eye Behavior Anomaly (staring, asymmetric pupil reflection)              13%   Eye synthesis + gaze modeling have improved significantly', '  #8  Eyebrow / Eyelash Artifacts (pencil-drawn look, repeated patterns)         6%   Rarely triggered in modern high-quality swaps', '  #6  Lip-Sync Error (mouth-audio temporal mismatch)                             2%   Wav2Lip-like audio-driven generation largely SOLVED this', '  #2  Face Stretch / Tear (non-physical deformation during motion)               1%   Modern swap geometric stability is EXCELLENT', '  #14 Background Object Misalignment (drift, sticking, distortion)               1%   Background stability is no longer a weakness'], 11),
    ]),
    # S24: Key Findings
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '6.3 关键发现：维度效能分化与趋势洞察', 26, True, AC),
        ('B', 0.6, 1.2, 12, 6, ['Finding 1: "Iron Triangle" reflects swap tech SYSTEMATIC WEAKNESSES.', '  Texture synthesis (#3=92%), mask edge blending (#1=91%), and color consistency (#4=90%) remain fundamentally unsolved problems', '  across all major face-swap frameworks (FaceSwap, DeepFaceLab, SimSwap, DiffFace, Roop).', '  These three dimensions alone can detect >90% of deepfake videos. -> Focus detection investment here.', '', 'Finding 2: Temporal inconsistency (#11=85%) CONFIRMS per-frame processing paradigm.', '  Most swap frameworks process frames independently without temporal coherence constraints.', '  High single-frame quality cannot mask frame-to-frame micro-fluctuations (face structure drift, sharpness flicker).', '  -> Temporal analysis is a high-signal detection direction with significant untapped potential.', '',
         'Finding 3: Biosignal dimensions show DIVERGENT evolution trajectories.', '  Micro-expression (#10=68%): Still robust. Multi-muscle facial dynamics remain AI-hard. -> Maintain as key indicator.', '  Eye behavior (#9=13%): Eye synthesis & gaze modeling have improved significantly in recent pipelines. -> Monitor decay trend.', '  Lip-sync (#6=2%): Wav2Lip-like audio-driven generation has LARGELY NEUTRALIZED this dimension. -> DOWNGRADE weight, do not rely on.', '  -> Prompt weighting should be DYNAMICALLY ADJUSTED as underlying swap technology capabilities evolve.', '',
         'Finding 4: Geometric stability is no longer a weakness (#2=1%, #14=1%).', '  Modern swap pipelines achieve high spatial consistency. Edge/blending indicators are now more reliable than geometric distortion indicators.'], 13),
    ]),
    # S25: Technical Methodology
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '7.1 技术方法论：四点核心认识', 30, True, AC),
        ('B', 0.8, 1.3, 11.5, 5.8, ['Four Core Technical Insights (transferable & generalizable):', '', 'I.  "Less is More" in VLM Prompt Design -- empirically validated.', '    21 items -> 0% recall  |  14 items -> 56% recall  |  18 items -> 33% recall', '    Non-monotonic relationship between prompt length and task accuracy.', '    Design principle: Focused instruction beats comprehensive enumeration. Verified via controlled experiments.', '    Implication: For any VLM multi-dimensional analysis task, start with the MINIMAL set and add only when necessary.', '', 'II. "Classical CV + VLM" Hybrid Paradigm -- the most impactful innovation.', '    VLM excels at semantic reasoning but has STRUCTURAL limitations in low-level visual feature perception.', '    Classical CV algorithms (Laplacian variance) fill this gap with precise mathematical quantification.', '    Solo VLM: 56% recall  ->  VLM+CV: 88-91% recall  (+32-35 percentage points).', '    This paradigm is broadly transferable to medical imaging, industrial defect detection, and other VLM perception-blind-spot domains.', '', 'III. Parameter Tuning as Systems Engineering -- the "last mile" from functional to effective.', '     Face-Neck ratio threshold 0.70 -> 0.85 (+21% delta) yielded +250% recall improvement.', '     Architecture correctness is only the STARTING POINT. Parameter OPTIMIZATION determines whether a system is "functional" or "effective".', '     This is often underappreciated in AI systems engineering but is critical for real-world deployment.', '', 'IV. Cost-Aware System Design -- dynamic resource allocation.', '     Two-stage voting: more verification votes for ambiguous cases, fewer for confirmed ones.', '     37% API cost reduction WITH accuracy improvement (Stage 2 corrected 2 missed cases).', '     Principle: Design the system to invest verification budget where it has the highest marginal value.'], 14),
    ]),
    # S26: AI Methodology
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '7.2 AI辅助编程方法论：三点核心认识', 28, True, GN),
        ('B', 0.8, 1.3, 11.5, 5.8, ['Three Core AI-Assisted Programming Insights (derived from 100+ interaction rounds):', '', 'I.  HUMAN PROVIDES THE JUDGMENT BASELINE -- this is the SINGLE most critical factor determining AI output quality.', '    Ground truth labels ("F2 is a DeepFake video"), quantitative metrics ("recall 56%->33%"),', '    and clear evaluation criteria are the HIGHEST-VALUE inputs to an AI coding assistant.', '    They define the "accuracy ceiling" of AI-generated solutions.', '    Without ground truth, AI can generate code but cannot judge if the code is producing CORRECT results.', '    With ground truth, AI can SELF-CALIBRATE and iteratively improve towards the target.', '', 'II. SIX INTERACTION PATTERNS form a replicable methodology framework for AI-assisted software engineering.', '    Different development phases call for different patterns:', '    Architecture design  -> Progressive Requirement Decomposition  (sequential, verifiable steps)', '    Debugging & diagnosis -> Hypothesis-Verification Loop           (scientific method applied to code)', '    Performance tuning   -> Anchored + Data-Driven Strategy         (quantitative feedback loops)', '    Strategy selection   -> Explore-Evaluate-Decide                  (multi-option analysis)', '    Innovation & ideation-> Metacognitive Guidance                  (AI self-review & propose)', '    These patterns are GENERALIZABLE beyond this specific project.', '', 'III. OPTIMAL HUMAN-AI COLLABORATION MODEL: "STRATEGIST-EXECUTOR".', '    Human: Goal setting, option selection, ground truth annotation, FINAL decisions.', '    AI:    Solution generation, code implementation, data mining, refinement iteration.', '    Complementary partnership, NOT replacement. The whole is greater than the sum of its parts.'], 14),
    ]),
    # S27: Limitations & Future
    (25,25,50, [
        ('T', 1, 0.5, 11, 0.7, '7.3 当前局限性与后续研究路线图', 28, True, AC),
        ('B', 0.5, 1.2, 6.2, 6, ['Current Limitations:', '', '1. Biosignal Decay', '   Lip-sync (#6:2%) & eye behavior', '   (#9:13%) losing discriminative', '   power. Continuous prompt iteration', '   needed as swap tech evolves.', '', '2. Face Detector Coverage', '   Haar Cascade limited for large-', '   angle profiles (>45 deg) and', '   heavy occlusion. MTCNN or', '   RetinaFace could improve recall.', '', '3. Temporal Analysis Depth', '   Currently only sharpness fluctuation,', '   no optical flow or motion analysis.', '   Missing high-value temporal signals.', '', '4. Offline Batch-Only', '   No real-time streaming, no Web', '   frontend, no REST API. Currently', '   CLI-only, limiting accessibility.'], 13),
        ('B', 7, 1.2, 5.5, 6, ['Future Research Roadmap:', '', 'Phase 1 -- Preprocessing Enhancement:', '  - LBP (Local Binary Patterns)', '    micro-texture quantification', '  - HSV/YCbCr color space separation', '    for channel-level anomaly detection', '  - Replace Haar Cascade with MTCNN', '', 'Phase 2 -- Temporal Analysis:', '  - RAFT optical flow for inter-frame', '    facial motion consistency analysis', '  - Lip-landmark trajectory tracking', '    for fine-grained sync verification', '  - 3D Morphable Model for facial', '    muscle movement modeling', '', 'Phase 3 -- Engineering & Deployment:', '  - FastAPI REST API + React Web UI', '  - Real-time streaming detection', '    pipeline with frame buffering', '  - Quarterly model re-evaluation', '    protocol for new VLM releases'], 13),
    ]),
    # S28: Conclusion
    (18,22,48, [
        ('T', 1.5, 0.4, 10.5, 1, '总结与致谢  Summary & Acknowledgments', 38, True, AC, PP_ALIGN.CENTER),
        ('B', 1.5, 2, 10, 3.5, ['Core Achievements:', '  Built VLM-based DeepFake detection system: 91% recall on 100 videos, 55.8 min, zero failures, 37% cost saving', '  Discovered and named the "Attention Dilution Effect" in VLM prompt engineering through controlled experiments', '  Designed Face-Neck Ratio mechanism to mathematically distinguish swap blur from beauty filter (threshold 0.85)', '  Established "Classical CV + VLM" hybrid paradigm: +32pp recall boost, broadly transferable to other perception domains', '  Developed 6-pattern AI-assisted programming methodology validated through 100+ interaction rounds', '', 'Two Independent Model Pipelines:', '  Development:   Claude Code CLI (frontend) + DeepSeek-V4-Pro [1M] (backend)   ->   AI-assisted code generation & debugging', '  Detection:     Python openai SDK (client) + Qwen3-VL-Plus (DashScope)        ->   Video forensic multi-dimensional analysis'], 16, WH),
        ('T', 1.5, 6.5, 10.5, 0.5, '计算机科学与技术专业  |  DeepFake Detection System v5.0  |  ' + datetime.now().strftime("%Y.%m"), 12, False, GR, PP_ALIGN.CENTER),
    ]),
]

for bg_r, bg_g, bg_b, elements in slides_data:
    s = make_slide(prs, (bg_r, bg_g, bg_b))
    for el in elements:
        if el[0] == 'T':
            T(s, *el[1:])
        elif el[0] == 'B':
            B(s, *el[1:])

prs.save('D:/DeepFake/本科综合实践PPT_DeepFake检测系统开发.pptx')
print('PPT done (28 slides).')
print('ALL COMPREHENSIVE FILES GENERATED SUCCESSFULLY.')
