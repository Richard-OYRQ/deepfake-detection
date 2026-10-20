# -*- coding: utf-8 -*-
"""生成《终裁层消融实验与v5.8配置说明》研究文档。
最终验证数据位于 FINAL 字典，验证完成后更新此处并重跑本脚本即可重新生成。"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ===================== 最终验证数据（2026-09-27 验证完成） =====================
FINAL = {
    # videos 校准分布 40 条（20真20伪）
    "v_base_fake_hit": "0/20", "v_v58_fake_hit": "5/20",
    "v_base_real_fp": "0/20",  "v_v58_real_fp": "0/20",
    "v_base_sus": "20",        "v_v58_sus": "17",
    # 外部评测分布 60 条（30真30伪）
    "e_base_fake_hit": "0/30", "e_v58_fake_hit": "1/30",
    "e_base_real_fp": "0/30",  "e_v58_real_fp": "0/30",
    "e_base_fake_miss": "21/30", "e_v58_fake_miss": "20/30",
    # 归因
    "conflict_recovered": "1", "backstop_new_convict": "6", "backstop_new_fp": "0",
}
# =====================================================================

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
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), name)


def title(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run(text), name="黑体", size=16, bold=True)
    p.paragraph_format.space_after = Pt(6)


def h1(text):
    p = doc.add_paragraph()
    set_font(p.add_run(text), name="黑体", size=14, bold=True, color=(0x1F, 0x4E, 0x79))
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)


def h2(text):
    p = doc.add_paragraph()
    set_font(p.add_run(text), name="黑体", size=12, bold=True, color=(0x2E, 0x74, 0xB5))
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)


def para(text, indent=True, bold=False):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    p.paragraph_format.line_spacing = 1.4
    set_font(p.add_run(text), bold=bold)
    return p


def table(headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = ""
        set_font(cell.paragraphs[0].add_run(h), name="黑体", size=10.5, bold=True)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            cell = t.rows[i].cells[j]
            cell.text = ""
            set_font(cell.paragraphs[0].add_run(str(v)), size=10.5)
    doc.add_paragraph()


def val(key, suffix=""):
    v = FINAL.get(key)
    return f"{v}{suffix}" if v is not None else "（待最终验证）"


# ===================== 正文 =====================
title("终裁层消融实验与 v5.8 配置说明")
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_font(p.add_run("2026-09-27"), name="宋体", size=10.5)

h1("一、背景")
para("判定策略 v5.7 的终裁层包含约 20 个策略参数：多个定罪阈值、守卫规则、路由豁免相互重叠。"
     "200 条校准集上存疑率 54.5%，exp6 纯伪造 6 条视频终裁全部为“存疑”（硬检出率 0%），"
     "其中三票全投换脸、证据分 3 的 F45 也因先验 0.46 未过 0.70 定罪背靠而被降级。"
     "为回答“终裁逻辑是否过度复杂”的问题，进行了零成本离线重放消融、现场 A/B 抽查与最终配对验证。")

h1("二、方法与数据")
para("离线重放：直接复用 processor.py 的 _finalize_result 终裁函数，对 full200 校准集（200 条带标签）"
     "与 exp6（6 条）的历史结果重放多组阈值变体，统计伪造检出、真实误报与存疑率，零 API 成本。", indent=False)
para("现场 A/B：外部评测集 40 条（20 真 20 伪），基线（v5.7）与去背靠版配对运行。", indent=False)
para("最终验证：videos 目录真伪各 20 条（排除 exp6 已用的 6 条）+ 外部评测集真伪各 30 条，共 100 条，"
     "v5.7 基线与 v5.8 在同一批视频上配对运行。", indent=False)
para("标签来源：videos/待鉴别按命名约定（F 开头=伪造、纯数字=真实），外部评测集按数据集目录标签。"
     "标签仅用于结果分析，检测流程不读取任何文件名信息。", indent=False)

h1("三、离线重放消融结论")
h2("3.1 死参数：20 个策略参数中 5 个从未生效")
para("prosecutor_convict_prior（0.75）：config 加载后代码中从未使用。"
     "prior_fake_threshold、prior_real_threshold、band_use_votes、phys_guard_convict："
     "仅在 auto_mode=true 分支生效，当前 auto_mode=false，全部空转。", indent=False)
h2("3.2 定罪背靠（backstop）是唯一有实质影响的旋钮")
table(["backstop 阈值", "伪造检出", "真实误报", "存疑(伪/真)"], [
    ["0.70（v5.7 现配置）", "31/106", "0/100", "57/5"],
    ["0.65", "41/106", "0/100", "47/5"],
    ["0.60", "45/106", "0/100", "43/5"],
    ["0.55", "52/106", "0/100", "36/5"],
    ["0.45", "66/106", "3/100", "22/2"],
    ["0.0", "73/106", "4/100", "15/1"],
])
para("0.70 被 0.55 严格占优：同样零误报下多捞回 21 条伪造。当初为治 84.mp4（先验 0.434）"
     "引入的背靠，0.45 即可挡住该案例，v5.7 一刀切到 0.70 属于过度防御。", indent=False)
h2("3.3 零贡献旋钮")
para("冲突阈值 0.55→0.45/0.70：只挪动 6-7 条存疑，硬判决零变化。"
     "置信度门槛 85/90→80/85：零变化（数据上非约束）。"
     "物理守卫：离线无法测（phys_score 未存档），现场 A/B 关闭后无可见差异。", indent=False)
h2("3.4 规则纠缠")
para("convict_prior 降至 0 反而使 exp6 检出 2/6→0/6：融合定罪的“控方轮→存疑”条款硬编码，"
     "闸门放低把更多记录送进控方→存疑通道。规则之间并非独立，这是终裁层过度复杂的最佳注脚。", indent=False)

h1("四、现场验证结果")
h2("4.1 A/B 抽查（外部评测集 40 条）")
para("基线：伪造检出 0/20、误报 0/20；去背靠版：检出 1/20、误报 1/20（R_729，先验 0.456）。"
     "外部伪造 15/20 走高清分支，单票定案 + CV 冲突豁免，16/20 伪造被硬判“无伪造”"
     "（其中 4 条先验≥0.55、最高 0.90）——“路由击穿”被实锤。", indent=False)
h2("4.2 最终配对验证（100 条，v5.7 vs v5.8）")
table(["分布", "指标", "v5.7 基线", "v5.8"], [
    ["videos 校准分布(40)", "伪造检出", val("v_base_fake_hit"), val("v_v58_fake_hit")],
    ["videos 校准分布(40)", "真实误报", val("v_base_real_fp"), val("v_v58_real_fp")],
    ["videos 校准分布(40)", "存疑", val("v_base_sus"), val("v_v58_sus")],
    ["外部评测分布(60)", "伪造检出", val("e_base_fake_hit"), val("e_v58_fake_hit")],
    ["外部评测分布(60)", "真实误报", val("e_base_real_fp"), val("e_v58_real_fp")],
    ["外部评测分布(60)", "伪造漏判(硬判无伪造)", val("e_base_fake_miss"), val("e_v58_fake_miss")],
])
para(f"归因：① 高清冲突豁免取消捞回高先验漏检 {val('conflict_recovered')} 条；"
     f"② backstop 0.55 新增定罪 {val('backstop_new_convict')} 条（其中真实误报 {val('backstop_new_fp')} 条）；"
     "③ 死参数清理不应产生任何判决变化。", indent=False)

h1("五、v5.8 配置变更清单")
para("1. prior_convict_backstop：0.70 → 0.55（消融实测 0.55 在校准集零误报且多捞 21 条伪造）。", indent=False)
para("2. 新增 highres_conflict_exempt: false：取消高清分支的 CV 冲突豁免"
     "（config.py 新增开关、processor.py 冲突规则尊重该开关，默认 true 维持旧行为）。", indent=False)
para("3. 清理死参数：删除 prosecutor_convict_prior、phys_guard_convict、"
     "prior_fake_threshold、prior_real_threshold、band_use_votes。", indent=False)
para("4. 其余不变：提示词、两阶段调用流程、流控、路由判定均与 v5.7 一致。", indent=False)

h1("六、结论与后续方向")
para("终裁层的复杂度大头已被证伪：20 个旋钮中 5 个是死的、4 个零贡献、1 个主导旋钮取值被占优。"
     "v5.8 以三个最小改动（背靠 0.55、取消高清冲突豁免、清理死参数）在维持零误报的前提下提升检出。"
     "但外部高清伪造的漏检瓶颈在模型检出能力与高清路由的单票机制，不在终裁阈值——"
     "后续方向：高清分支引入复检轮；提示词层针对高质量换脸的改进；"
     "av 库补装后恢复唇同步量化；以及在 550+550 全量评测集上做最终基准。", indent=False)

out = r"E:\deepfake\研究文档\20260927_终裁层消融实验与v5.8配置说明.docx"
doc.save(out)
print("已生成:", out)
