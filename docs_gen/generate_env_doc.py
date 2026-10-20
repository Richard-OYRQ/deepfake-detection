# -*- coding: utf-8 -*-
"""生成《检测环境构成与使用说明》文档（约3000字）。"""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def set_font(run, name='微软雅黑', size=11, bold=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def h1(doc, text):
    p = doc.add_heading(level=1)
    set_font(p.add_run(text), size=15, bold=True, color=(0x1F, 0x4E, 0x79))


def h2(doc, text):
    p = doc.add_heading(level=2)
    set_font(p.add_run(text), size=12.5, bold=True, color=(0x2E, 0x74, 0xB5))


def para(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(22)
    set_font(p.add_run(text), size=11)
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    set_font(p.add_run(text), size=11)


def table(doc, headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Light Grid Accent 1'
    for j, htext in enumerate(headers):
        cell = t.rows[0].cells[j]
        set_font(cell.paragraphs[0].add_run(htext), size=10, bold=True)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            set_font(cell.paragraphs[0].add_run(str(val)), size=10)
    doc.add_paragraph()


doc = Document()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run('AI换脸检测系统：环境构成与使用说明'), size=20, bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run('（v5.7生产配置，2026年8月）'), size=12, color=(0x66, 0x66, 0x66))

# ============ 一、环境构成 ============
h1(doc, '一、检测环境的主要构成')
para(doc, '检测系统由"本地电脑 + 云端大模型API + 本地Python程序"三部分组成：本地电脑负责运行Python检测程序与OpenCV像素分析；云端通过千问大模型API提供视觉检测能力；Python程序是连接两者的中枢，负责视频预处理、请求调度、结果融合与报告生成。系统整体架构分五层：预处理层、先验层、提示词层、路由与投票层、终裁层。')
table(doc,
      ['组件', '所在位置', '作用'],
      [
          ['Python检测程序（main.py + src/六模块）', '本地', '调度中枢：批量读取、请求管理、终裁融合、结果存储'],
          ['OpenCV（opencv-python 4.14）', '本地', '像素分析：抽帧、清晰度量化、物理特征、证据图生成'],
          ['千问视觉大模型（qwen3-vl-plus）', '云端API', '视觉检测：16项逐项取证、控方复核、可视化核验'],
          ['先验模型（prior_model双文件）', '本地', 'P(伪造|特征)估计，双先验max融合'],
          ['配置与数据（config.yaml、200标注集、14对配对集）', '本地', '参数驱动与评估基准'],
          ['辅助工具（FaceFusion独立venv、ffmpeg便携版、PyAV）', '本地', '配对样本生成与实验支撑'],
          ['研发编程环境（Claude Code + DeepSeek-V4-Pro）', '本地CLI+云端', '自然语言驱动的代码生成、调试与文档产出'],
      ])

# ============ 二、后端 ============
h1(doc, '二、后端支撑的编程环境与视频检测大模型')
h2(doc, '2.1 编程环境')
para(doc, '后端程序采用Python 3.14编写，核心依赖：openai（千问API的OpenAI兼容调用）、opencv-python 4.14（图像处理）、pyyaml（配置解析）、python-dotenv（环境变量）。项目采用config.yaml配置驱动、模块分离架构：src/config.py（配置）、src/client.py（API客户端）、src/rate_limiter.py（限流重试）、src/processor.py（处理编排）、src/preprocessor.py（预处理与先验）、src/formatter.py（输出与增量保存）。另配Python 3.12环境与FaceFusion独立venv（钉死opencv-python-headless 5.0）用于换脸样本生成，两个环境严格隔离。')
h2(doc, '2.2 视频检测大模型')
para(doc, '检测模型为通义千问qwen3-vl-plus（视觉语言大模型，支持视频输入与结构化输出）。模型经四款比选选定：真实视频零误报、基准集检出率80%，能有效利用预处理量化数据而不被过度引导。请求参数：温度0.7、最大生成长度8192、超时300秒；视频输入支持base64内联（≤15MiB）、上传签名URL（大文件）、直连URL三种方式。')
h2(doc, '2.3 API申请方法')
para(doc, '申请步骤：①注册阿里云账号并实名认证；②进入阿里云百炼（Model Studio）控制台；③开通"百炼大模型服务"并同意服务协议；④在"API-KEY管理"页面创建API密钥并妥善保存；⑤将密钥填入项目config.yaml的api_key字段（或.env文件）。计费方式为按token计费，qwen3-vl-plus单价约0.001元/千输入token，200视频全量检测约16元。')

# ============ 三、研发编程环境 ============
h1(doc, '三、研发编程环境：Claude Code框架 + DeepSeek编程大模型')
h2(doc, '3.1 组件构成与作用')
para(doc, '检测系统本身是"被检测程序"，而研发这套程序的环境还有另一对重要组件——AI编程助手：Claude Code（编程框架/工作台）与DeepSeek-V4-Pro（编程大模型后端）。两者的关系类似于"驾驶员与发动机"：Claude Code提供命令行交互框架，负责理解开发者指令、读写本地文件、执行命令、管理任务上下文；DeepSeek-V4-Pro作为后端大模型负责实际生成与迭代代码。该组合的核心优势是DeepSeek-V4-Pro支持1M（百万token）上下文窗口——可以一次性装载整个项目的代码与历史对话，实现"全局视野"下的跨文件修改，这是检测系统十周内完成六版迭代的重要支撑。')
note = doc.add_paragraph()
note.paragraph_format.first_line_indent = Pt(0)
set_font(note.add_run('【知识备注】Claude Code=一种AI编程框架（命令行工具），可以把"用自然语言指挥AI写代码"变成工作流；DeepSeek=国产大模型，V4-Pro是其支持超长上下文的版本；token=大模型处理文本的最小单位，1M token约等于一部《三体》的篇幅。'), size=9.5, color=(0x8B, 0x45, 0x13))
h2(doc, '3.2 安装配置')
para(doc, '安装配置过程：①安装Node.js运行时（Claude Code的运行基础）；②通过npm安装Claude Code命令行工具（npm install -g @anthropic-ai/claude-code）；③配置后端模型接入DeepSeek——在配置文件中将模型端点指向DeepSeek的API接口（与千问API类似，均为OpenAI兼容格式），填入DeepSeek API密钥；④在项目目录启动Claude Code（claude命令），即进入"对话式开发"工作台。配置完成后，开发者用中文自然语言描述需求，Claude Code调用DeepSeek生成代码、写入文件并执行验证。')
h2(doc, '3.3 检测系统的编程研发过程')
para(doc, '本检测系统的全部代码（约三千行Python）均以"自然语言驱动"方式在Claude Code+DeepSeek环境中完成，未逐行手写复杂代码。研发过程呈现典型的对话式迭代节奏：')
bullet(doc, '摸底阶段：让AI通读项目现状（"请分析当前检测系统的架构"），由其梳理模块结构与改进点；')
bullet(doc, '改造阶段：以需求描述驱动开发（"把投票机制改成对称对抗投票""增加遮挡边缘衰减特征"），AI生成代码→本地运行→用200标注集验证→把验证数据反馈给AI→再迭代；')
bullet(doc, '调试阶段：报错信息与日志直接粘贴给AI定位修复（如data-uri体积超限、cv2版本冲突、静默失败排查）；')
bullet(doc, '文档阶段：全部报告与PPT由AI按"数据+模板"批量生成，本次环境说明文档同样由该环境产出。')
para(doc, '研发过程中的关键分工纪律：AI提供方案与代码，实验数据担任裁判——AI推荐的每个方案（如"无罪推定提示词""控方轮"）都必须先跑实验验证再决定采纳与否。项目后期八组提示词实验七组无效的经历证明：AI方案需要数据检验，不能照单全收。')
h2(doc, '3.4 操作使用方法（对话式开发）')
bullet(doc, '启动：在项目目录运行claude，进入交互界面；')
bullet(doc, '提问式开发："帮我写一个……""这个报错是什么原因""把config.yaml里的阈值改到0.6"；')
bullet(doc, '长任务后台化：批量检测、特征表重建等耗时任务交给后台执行，AI负责监控与汇总；')
bullet(doc, '记忆与复用：关键结论写入项目记忆文件，下次对话自动加载——项目全过程的知识资产由此沉淀。')

# ============ 四、前端设备 ============
h1(doc, '四、前端电脑设备')
para(doc, '本项目运行于普通笔记本电脑：Windows 11操作系统、16GB内存、Intel集成显卡（无独立GPU）。设备特性对系统设计产生了两点影响：其一，视频解码存在非确定性，先验计算需采用"三次计算取中位数"的稳定化机制；其二，无GPU使FaceFusion换脸仅能CPU推理（约10分钟/15秒视频），配对样本生成以后台批量方式运行。检测主程序对算力要求低（OpenCV CPU即可），全部重计算集中在云端API侧。')

# ============ 四、组件协作 ============
h1(doc, '五、组件部署与相互协作关系')
para(doc, '各组件的协作流程（检测一个视频）：①config.yaml载入全部参数；②preprocessor执行抽帧与清晰度量化（OpenCV），计算先验（本地逻辑回归模型，双先验max融合）；③按分辨率路由——高清视频（≥1280×720）由保守模型票直接终裁，低清视频进入完整流程；④client按限流规则（每分钟5次、并发2）向云端API发送视频与提示词（16项主提示词/14项控方提示词），并随附事件证据图与CV可视化证据图；⑤processor对返回的逐项判定表与核验行做解析，按六信号终裁规则（先验、物理守卫、证据子分、控方票、可视化核验、票型）输出三分类（无伪造/伪造/存疑）；⑥formatter将结果写入JSON与Markdown并增量保存。')
table(doc,
      ['环节', '负责组件', '输入', '输出'],
      [
          ['预处理', 'OpenCV+preprocessor', '视频文件', '量化特征+先验+证据图'],
          ['路由', 'processor', '分辨率+先验', '分支选择'],
          ['视觉检测', '云端qwen3-vl-plus', '视频+提示词+证据图', '逐项判定+核验行'],
          ['信号解析', 'processor', '模型返回文本', '票型+证据子分+核验结论'],
          ['终裁', 'processor', '六信号', '三分类判定'],
          ['留档', 'formatter', '判定结果', 'JSON+Markdown+增量日志'],
      ])

# ============ 五、搭建过程 ============
h1(doc, '六、搭建过程与方法')
bullet(doc, '第一步：安装Python 3.14，pip安装openai/opencv-python/pyyaml/python-dotenv（国内可配清华镜像加速）；')
bullet(doc, '第二步：申请千问API密钥（见2.3），填入config.yaml，用单个小视频调试请求通断；')
bullet(doc, '第三步：组织数据集目录（videos/真实、待鉴别/伪造），运行python main.py --dry-run校验配置；')
bullet(doc, '第四步：（可选）生成配对样本：另装Python 3.12并建FaceFusion独立venv，下载ffmpeg便携版，按pairset/plan.json批量生成换脸视频；')
bullet(doc, '第五步：批量检测python main.py --config config.yaml，结果自动存output/并按日期留档。')
para(doc, '踩坑备忘：data-uri上限20MiB（大文件走上传通道）；opencv 5.0与4.14不可共存需环境隔离；人脸检测在边缘样本上随机失败需合并机制；模型API密钥严禁外传。')

# ============ 六、使用说明 ============
h1(doc, '七、操作使用方法')
bullet(doc, '全量检测：python main.py --config config_full200.yaml（约520次请求/16元/3-4小时，支持断点增量保存）；')
bullet(doc, '单/少量视频：将视频放入目录后指定videos.dir，或使用config_v3.yaml等小型配置；')
bullet(doc, '切换提示词/阈值：直接编辑config.yaml对应字段（无需改代码），改后运行--dry-run校验；')
bullet(doc, '结果查看：output/目录results_*.json（结构化判定）与run_*.md（可读报告），200视频明细见200视频检测明细.csv；')
bullet(doc, '关键配置开关：route_highres（自适应路由）、cv_visual_evidence（CV可视化证据）、prior_anchor_table（先验锚定）、prior_convict_backstop（定罪背书0.70）、prior_fake_threshold（全自动阈值0.60）。')

h1(doc, '八、常见问题排查')
bullet(doc, '请求报"Exceeded limit on max bytes per data-uri item"：视频超过15MiB走了base64内联，确认走上传通道或压缩视频；')
bullet(doc, '限流报错（429）：检查限流参数（每分钟5次、并发2），等待重试即可，程序已内置指数退避；')
bullet(doc, '人脸检测全失败：视频可能无人脸或为侧脸，属正常（如96.mp4/F88.mp4），构建脚本已内置缺失合并机制；')
bullet(doc, '先验值与表值差异大：解码非确定性所致，生产配置已开启prior_anchor_table锚定；')
bullet(doc, 'FaceFusion输出与原视频一致（静默失败）：换脸未生效，用"输出帧vs原帧直接比对"验证法确认，必要时更换目标视频。')

doc.save(r'D:\deepfake\鉴伪实践项目\检测环境构成与使用说明_20260830.docx')
print('saved')
