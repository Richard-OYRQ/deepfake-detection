# -*- coding: utf-8 -*-
"""生成《检测环境迁移部署指南》（旧机→HP OMEN 16）。"""
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


def note(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    set_font(p.add_run('【说明】' + text), size=9.5, color=(0x8B, 0x45, 0x13))
    return p


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
set_font(p.add_run('检测环境迁移部署指南'), size=20, bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run('——从原笔记本迁移至惠普HyperX暗影精灵Pro 16（OMEN 16-am2071tx）'), size=12, color=(0x66, 0x66, 0x66))

# ============ 一、迁移清单 ============
h1(doc, '一、迁移清单（先确认要搬什么）')
table(doc,
      ['内容', '原位置', '大小', '迁移方式'],
      [
          ['项目主体（代码/配置/模型/特征表/结果/文档）', 'D:\\deepfake 全部', '数GB（视频为主）', '整目录复制'],
          ['ffmpeg/ffprobe 便携版', 'D:\\facefusion\\bin', '约155MB', '整目录复制'],
          ['FaceFusion 源码', 'D:\\facefusion\\facefusion-master', '约50MB', '整目录复制'],
          ['Python 3.14 依赖', '需在新机重装', '—', 'pip 镜像安装'],
          ['Python 3.12 + ffvenv', '不能复制', '—', '新机重建'],
      ])
note(doc, 'venv（虚拟环境）绑定绝对路径，直接复制到新机会失效，必须重建。这是迁移中最常见的坑。')

# ============ 二、部署步骤 ============
h1(doc, '二、部署步骤（按顺序执行）')
h2(doc, '第1步：复制数据与程序')
para(doc, '用移动硬盘或局域网把 D:\\deepfake 与 D:\\facefusion 两个目录整体复制到新机D盘相同路径（保持 D:\\deepfake 结构不变，脚本里的绝对路径即可免改）。大数据量推荐使用 robocopy 命令（按 Win+R 输入 cmd 回车后执行）：')
note(doc, 'robocopy D:\\deepfake E:\\deepfake /E  表示把D盘deepfake文件夹完整复制到E盘（/E包含所有子文件夹）。它比普通复制快、支持断点续传、遇到个别坏文件跳过继续。用普通复制粘贴也可以，拷完抽查几个视频能打开即可。')
para(doc, '复制完成后抽查：随机打开几个视频文件、打开 output 下任一结果 JSON，确认数据完整。')
h2(doc, '第2步：安装 Python 双环境')
bullet(doc, '安装 Python 3.14 与 Python 3.12（官网安装包或 winget，安装时勾选加入PATH）；')
bullet(doc, '配置清华pip镜像：pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple')
h2(doc, '第3步：恢复项目环境（Python 3.14）')
note(doc, '在cmd中执行：py -3.14 -m pip install openai "opencv-python<5" pyyaml python-dotenv numpy matplotlib python-docx python-pptx av')
para(doc, '其中：openai=千问API调用库；opencv-python<5=像素分析（必须4.x版本，5.0缺少人脸检测器）；av=PyAV音频解码库。如项目后续用到其他依赖，可对照旧机 pip list 补装。')
h2(doc, '第4步：重建 FaceFusion 环境（Python 3.12 + 新venv）')
note(doc, '依次执行：\npy -3.12 -m venv D:\\facefusion\\ffvenv\nD:\\facefusion\\ffvenv\\Scripts\\python -m pip install -r D:\\facefusion\\facefusion-master\\requirements.txt')
h2(doc, '第5步：验证检测系统')
note(doc, '在 D:\\deepfake 目录执行：\npython main.py --config config_v3.yaml --dry-run   （配置校验，不发请求）\npython main.py --config config_v3.yaml              （3视频小实测，约0.4元）')
para(doc, 'dry-run 通过且小实测正常返回结果，即迁移成功。')
h2(doc, '第6步（可选）：开启 RTX 5060 加速')
bullet(doc, 'FaceFusion：ffvenv 中换装 onnxruntime-gpu（Blackwell 架构需 1.20 以上版本配 CUDA 12），换脸生成从约10分钟/段降至约1分钟/段；')
bullet(doc, 'CNN检测器（后续）：安装 PyTorch cu128 版，本地训练 EfficientNet。')
h2(doc, '第7步（可选）：恢复 AI 编程环境')
para(doc, '新机安装 Node.js → 命令行执行 npm install -g @anthropic-ai/claude-code → 配置 DeepSeek 后端接入 → 在 D:\\deepfake 目录启动 claude，即恢复"自然语言驱动开发"工作台。')

# ============ 三、关键提醒 ============
h1(doc, '三、三个关键提醒')
bullet(doc, 'venv 不能复制：ffvenv 必须在新机重建，否则 FaceFusion 无法启动；')
bullet(doc, '路径必须一致：全部脚本硬编码了 D:\\deepfake 与 D:\\facefusion，新机使用相同盘符路径可免改配置；若只能用其他盘符，需全局替换脚本与config中的路径；')
bullet(doc, '硬链接目录变普通文件无碍：_full200、_paircmp 等临时目录复制后变成独立文件（多占约10GB空间），功能不受影响，介意的话迁移后删除这些目录即可。')

# ============ 四、验证清单 ============
h1(doc, '四、迁移完成验证清单')
table(doc,
      ['检查项', '通过标准'],
      [
          ['Python 3.14 依赖', 'python -c "import cv2, openai, yaml" 无报错，cv2版本为4.x'],
          ['配置校验', 'main.py --dry-run 通过并正确列出视频任务'],
          ['API连通', '3视频小实测返回结构化判定结果'],
          ['FaceFusion', 'ffvenv 的 python -c "import cv2" 显示5.0版本，headless-run --help 可执行'],
          ['ffmpeg', 'cmd 输入 ffmpeg -version 显示版本号'],
          ['数据完整性', '200标注集与pairset目录视频均可打开'],
      ])

doc.save(r'D:\deepfake\鉴伪实践项目\检测环境迁移部署指南_20260830.docx')
print('saved')
