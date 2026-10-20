# -*- coding: utf-8 -*-
"""生成《专用CNN/Transformer深度伪造检测器建设方案》。"""
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
set_font(p.add_run('专用CNN/Transformer深度伪造检测器建设方案'), size=20, bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run('——大模型级联架构的方案B环节（2026年8月30日）'), size=12, color=(0x66, 0x66, 0x66))

# ============ 一、背景 ============
h1(doc, '一、背景与依据')
para(doc, '本项目前期工作已严格证明：通义千问视觉大模型（qwen3-vl-plus）对换脸外观指纹的感知存在能力边界——八组实验显示其对细纹理伪影零判别，唯一有效的模型通道用法是"CV可视化重编码+视频核验"（敏感性46%、特异性93%，两轮复现）。因此，在追求更高检测精度的方向上，需要引入专门为深度伪造检测设计的检测器。')
para(doc, '外部能力评估报告（千问视觉大模型Qwen3.docx）推荐的方案B正是本方案的设计依据：专用CNN/Transformer检测器负责高灵敏度初筛，大模型对高可疑样本生成可解释报告（"二次会诊"），综合决策系统融合多路信号。学术界证据同样支持该路线：FaceForensics++等基准上专用检测器显著优于通用多模态模型；研究明确指出"通用多模态表示对微妙几何与纹理伪影敏感度不足"。本方案即为方案B第一环（专用检测器）的完整建设计划。')

# ============ 二、总体设计 ============
h1(doc, '二、总体设计')
para(doc, '检测器定位：帧级二分类器（真实人脸/换脸人脸），输入为对齐后的人脸裁剪图（224×224），视频级判定由帧级分数聚合产生。整体级联形态：')
bullet(doc, '第一级：专用检测器逐帧推理 → 视频级伪造概率；')
bullet(doc, '第二级：概率≥阈值的高可疑视频 → qwen3-vl-plus 生成可解释鉴伪报告（复用现有v5.6核验通道）；')
bullet(doc, '第三级：综合决策——检测器概率 + CV先验 + 模型核验三路融合，输出三分类（无伪造/伪造/存疑）。')
para(doc, '现有资产复用清单：200标注视频（训练/验证数据）、14对1080P配对基准集（跨工具泛化评估）、FaceFusion生成管线（训练数据扩充）、CV特征库（软化系/物理特征，可作级联特征或辅助输入）、v5.6模型核验通道（会诊环节）。')

# ============ 三、数据准备 ============
h1(doc, '三、数据准备（工作量最大的一环）')
h2(doc, '3.1 训练数据扩充')
para(doc, '200个视频规模不足以训练专用检测器，目标为1000~2000个换脸样本：用现有FaceFusion管线批量生成（本机CPU约10分钟/视频，后台运行数天可产出数百个）；换脸工具多样化——除inswapper外引入不同模型参数组合，避免检测器只学习单一工具的指纹；真实视频负样本使用videos/目录100个视频并可按需补充采集。')
h2(doc, '3.2 人脸对齐与裁剪')
para(doc, '专用检测器的标准输入是"对齐后的人脸裁剪"而非整帧：引入人脸关键点检测器（mediapipe或2DFAN，需新装依赖）；从每帧检测人脸并按关键点对齐到统一模板（224×224）；对无脸帧跳过、对多脸帧取最大人脸。')
h2(doc, '3.3 数据集划分（防泄漏铁律）')
para(doc, '按人物划分训练/验证/测试集——同一人物的真脸与换脸不得跨集出现，否则检测器学到的将是"认人"而非"认伪造"。建议比例8:1:1，并保证测试集包含未见人物的真假对。')
h2(doc, '3.4 数据增强')
para(doc, '模拟真实场景的退化：JPEG压缩、高斯模糊、分辨率降采样、亮度对比度扰动——提升检测器跨画质泛化能力（对应本项目已发现的源质量混淆问题，训练数据需覆盖质量分布）。')

# ============ 四、模型选择 ============
h1(doc, '四、模型架构选择')
table(doc,
      ['路线', '方案', '说明'],
      [
          ['帧级（推荐起步）', 'Xception / EfficientNet-B4', 'FaceForensics++经典基线，ImageNet预训练微调，云GPU数小时可训'],
          ['视频级', '帧特征+LSTM/GRU聚合 或 TimeSformer', '利用帧间信息，数据需求更高，二期考虑'],
          ['轻量起步', 'MobileNet-V3', '本机CPU可慢训，用于先验证数据管线与评估流程'],
      ])

# ============ 五、训练设施 ============
h1(doc, '五、训练基础设施')
bullet(doc, '算力：本机无独立GPU，租用云GPU（AutoDL等平台，RTX 3090约1~2元/小时）；')
bullet(doc, '框架：PyTorch（云GPU环境现装），训练技巧包括ImageNet预训练权重、类别加权、Focal Loss、早停与学习率调度；')
bullet(doc, '评估指标：准确率、召回率、AUC、EER；关键评估环节为14对配对基准集上的跨工具泛化测试；')
bullet(doc, '成本估算：数据管线1周（生成零成本），云GPU训练与调参1~2周（约50~100元），级联集成3~5天（零成本复用现有脚本）。')

# ============ 六、级联集成 ============
h1(doc, '六、与现有系统的级联集成')
para(doc, '集成接口设计：专用检测器输出视频级伪造概率P_det；融合规则初版——P_det≥0.8直接判伪造（高置信）、0.3~0.8进入大模型会诊（v5.6核验通道）与CV先验交叉验证、<0.3判无伪造。融合决策表在200标注集与14对配对集上校准阈值，保证硬误报不高于现行水平。')

# ============ 七、风险 ============
h1(doc, '七、风险提示')
bullet(doc, '过拟合换脸工具：只训inswapper样本的检测器可能对其他工具失效——配对集跨工具测试是必过关卡；')
bullet(doc, '数据泄漏：按人物划分铁律，违反则指标虚高；')
bullet(doc, '定位建议：本项目以"演示级方案B"为定位——小规模数据（500~1000样本）+预训练微调+在14对配对集上展示"专用检测器vs大模型"的性能对比，预期检测器在软化指纹类伪影上显著优于大模型，该对比本身即为高价值结题素材。')

# ============ 八、计划 ============
h1(doc, '八、实施计划')
table(doc,
      ['阶段', '任务', '周期', '成本'],
      [
          ['1', '人脸对齐数据管线搭建（landmark依赖、裁剪、划分、增强）', '1周', '0元'],
          ['2', 'FaceFusion批量扩充训练数据（后台生成）', '并行', '0元'],
          ['3', '云GPU训练EfficientNet/Xception与调参', '1~2周', '50~100元'],
          ['4', '配对集泛化评估 + 级联集成 + 阈值校准', '3~5天', '0元'],
          ['5', '检测器vs大模型对比实验与报告归档', '2天', '0元'],
      ])

doc.save(r'D:\deepfake\鉴伪实践项目\专用CNN检测器建设方案_20260830.docx')
print('saved')
