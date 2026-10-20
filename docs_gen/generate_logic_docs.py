# -*- coding: utf-8 -*-
"""生成两版检测逻辑说明文档：v5.7 原版 与 v5.8 现行版，结构平行便于对照。"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_V57 = r"E:\deepfake\研究文档\20260927_检测逻辑说明_v5.7原版_v2.docx"
OUT_V58 = r"E:\deepfake\研究文档\20260927_检测逻辑说明_v5.8现行版_v2.docx"


def build_doc(title, version_note, flow_items, verdict_rules, param_rows,
              tail_title, tail_paras, out_path):
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

    def h1(text):
        p = doc.add_paragraph()
        set_font(p.add_run(text), name="黑体", size=14, bold=True, color=(0x1F, 0x4E, 0x79))
        p.paragraph_format.space_before = Pt(10)

    def h2(text):
        p = doc.add_paragraph()
        set_font(p.add_run(text), name="黑体", size=12, bold=True, color=(0x2E, 0x74, 0xB5))
        p.paragraph_format.space_before = Pt(6)

    def para(text, indent=True, bold=False):
        p = doc.add_paragraph()
        if indent:
            p.paragraph_format.first_line_indent = Pt(24)
        p.paragraph_format.line_spacing = 1.4
        set_font(p.add_run(text), bold=bold)

    def table(headers, rows, size=10.5):
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

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run(title), name="黑体", size=16, bold=True)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run(version_note), size=10.5)

    h1("一、系统组成")
    para("视觉大模型（qwen3-vl-plus，逐帧检查 16 项面部线索并投票）+ 计算机视觉预处理"
         "（清晰度/面颈比/物理特征量化，输出 CV 先验分数与证据图）+ 判决层（终裁规则）。"
         "流控：并发 2、每分钟 5 次请求、失败重试 3 次（指数退避）。")

    h1("二、单条视频检测流程")
    for i, item in enumerate(flow_items, 1):
        para(f"{i}. {item}", indent=False)

    h1("三、终裁规则")
    table(["顺序", "条件", "结论"], verdict_rules)

    h1("四、策略参数清单")
    table(["参数", "取值", "作用", "状态"], param_rows)
    active = sum(1 for r in param_rows if r[3] == "生效")
    dead = sum(1 for r in param_rows if r[3] == "死参数")
    para(f"共 {len(param_rows)} 项阈值/开关参数：生效 {active} 项，死参数 {dead} 项。", indent=False)

    h1(tail_title)
    for t in tail_paras:
        para(t)

    doc.save(out_path)
    print("已生成:", out_path)


# ============ 公共流程（两版一致） ============
FLOW = [
"预处理：均匀抽帧（4–16 帧）→ Haar 人脸检测 → 面部/颈部清晰度与面颈比测量 → 物理特征测量 → "
"生成事件证据图（遮挡交界放大、转动序列、帧差增强）与 CV 可视化证据图（纹理热力图+面颈剖面，仅低清附加）",
"先验计算：双先验模型融合取高值（max）→ 同一视频三次计算取中位数（抑制 ±0.2 解码波动）→ "
"先验锚定表校正（实时先验与官方表值偏差超过 0.15 时改用表值）",
"路由分流：分辨率 ≥1280×720 走高清分支（模型主导），否则走低清分支（CV 主导）。"
"路由仅决定检测通道，不参与判决",
"阶段一初筛：16 项主提示词一票初筛（无罪推定 + 美颜辨析表 + 软/硬/物理三级证据分级）",
"阶段二复检（3 票）：高清分支跳过复检、单票直接终裁；低清分支按初筛结果触发——"
"初筛“伪造”且置信度 <90 → 辩护人对抗复检（追加辩方提示词，逐条找良性解释）；"
"初筛“无伪造”且先验 >0.55 → 控方对抗复核（整段替换为激进版提示词）",
"复检定案：3 票多数票为最终票型，覆盖初筛结果",
"终裁：按第三节规则表输出 伪造 / 无伪造 / 存疑（三分类）",
"输出：逐视频增量保存（断点续跑），生成 JSON 与 Markdown 双格式报告",
]

# ============ v5.7 ============
VERDICT_V57 = [
["1", "复检票型存在任一伪造票（换脸/面部重演/全生成）且先验 ≥ 0.70", "伪造（融合定罪）"],
["2", "规则1中若为控方轮票型", "存疑（控方轮只做捞回，不定罪）"],
["3", "票型分裂（多种结论并存）", "存疑"],
["4", "视觉判“无伪造”但先验 ≥ 0.55（高清分支豁免）", "存疑（视觉与量化冲突）"],
["5", "视觉判“无伪造”且物理证据子分 ≥ 0.5（高清豁免）", "存疑（物理证据守卫）"],
["6", "视觉判“无伪造”且控方证据表异常项 ≥ 3（高清豁免）", "存疑"],
["7", "视觉判“无伪造”且面颈纹理跳变核验=“支持”（高清豁免）", "存疑（CV可视化核验）"],
["8", "视觉判“无伪造”且置信度 ≥ 90", "无伪造"],
["9", "视觉判“无伪造”但置信度 < 90", "存疑"],
["10", "视觉判伪造且置信度 ≥ 85 且先验 ≥ 0.70（定罪背靠）", "伪造"],
["11", "视觉判伪造但不满足规则10", "存疑"],
]

PARAMS_V57 = [
["auto_mode", "false", "三分类模式（含存疑人工复核）", "生效"],
["prior_fake_threshold", "0.60", "全自动：先验≥此值硬判伪造", "死参数"],
["prior_real_threshold", "0.45", "全自动：先验<此值硬判无伪造", "死参数"],
["band_use_votes", "true", "全自动：边界带内用模型票微调", "死参数"],
["fake_recheck_conf_threshold", "90", "初筛伪造且置信度<此值→辩护人复检", "生效"],
["final_fake_conf_threshold", "85", "终裁伪造所需最低置信度", "生效"],
["final_real_conf_threshold", "90", "终裁无伪造所需最低置信度", "生效"],
["suspicious_on_vote_split", "true", "票型分裂→存疑", "生效"],
["prior_high_threshold", "0.55", "初筛无伪造且先验>此值→控方轮", "生效"],
["prior_conflict_threshold", "0.55", "视觉无伪造+先验≥此值→存疑", "生效"],
["prosecutor_convict_prior", "0.75", "控方轮定罪先验门槛", "死参数"],
["convict_prior", "0.70", "融合定罪先验门槛", "生效"],
["attach_event_frames", "true", "送检附加事件证据图", "生效"],
["prior_fusion", "max", "双先验融合取高值", "生效"],
["phys_guard_threshold", "0.5", "物理证据守卫：子分≥此值至少存疑", "生效"],
["phys_guard_convict", "0.0", "全自动：物理守卫定罪门槛", "死参数"],
["route_highres", "true", "≥720P 走模型主导分支", "生效"],
["highres_min_width", "1280", "高清分支最小宽度", "生效"],
["highres_min_height", "720", "高清分支最小高度", "生效"],
["item_evidence_threshold", "3", "控方证据子分定罪/存疑阈值", "生效"],
["cv_visual_evidence", "true", "低清附加CV可视化证据图", "生效"],
["prior_anchor_table", "true", "实时先验锚定表值校正", "生效"],
["prior_convict_backstop", "0.70", "定罪背靠：伪造票定罪所需先验", "生效"],
]

V57_TAIL = "五、已知问题（v5.8 修复动因）"
V57_TAIL_PARAS = [
"1. 过度保守：200 条校准集存疑率 54.5%；exp6 纯伪造 6 条终裁全部“存疑”，硬检出率 0%。",
"2. 路由击穿：外部评测集高清伪造 16/20 被直接判“无伪造”——高清分支单票定案且冲突复查豁免，"
"其中 4 条先验 0.55~0.90 的样本被放行。",
"3. 参数冗余：23 项参数中 5 项死参数；消融实验证实冲突阈值、置信度门槛等旋钮硬判决零贡献。",
"4. 规则纠缠：融合定罪闸门降低反而使检出下降（控方轮→存疑条款硬编码）。",
]

# ============ v5.8 ============
VERDICT_V58 = [
["1", "复检票型存在任一伪造票（换脸/面部重演/全生成）且先验 ≥ 0.70", "伪造（融合定罪）"],
["2", "规则1中若为控方轮票型", "存疑（控方轮只做捞回，不定罪）"],
["3", "票型分裂（多种结论并存）", "存疑"],
["4", "视觉判“无伪造”但先验 ≥ 0.55（含高清，豁免已取消）", "存疑（视觉与量化冲突）"],
["5", "视觉判“无伪造”且物理证据子分 ≥ 0.5（高清豁免）", "存疑（物理证据守卫）"],
["6", "视觉判“无伪造”且控方证据表异常项 ≥ 3（高清豁免）", "存疑"],
["7", "视觉判“无伪造”且面颈纹理跳变核验=“支持”（高清豁免）", "存疑（CV可视化核验）"],
["8", "视觉判“无伪造”且置信度 ≥ 90", "无伪造"],
["9", "视觉判“无伪造”但置信度 < 90", "存疑"],
["10", "视觉判伪造且置信度 ≥ 85 且先验 ≥ 0.55（定罪背靠）", "伪造"],
["11", "视觉判伪造但不满足规则10", "存疑"],
]

PARAMS_V58 = [
["auto_mode", "false", "三分类模式（含存疑人工复核）", "生效"],
["fake_recheck_conf_threshold", "90", "初筛伪造且置信度<此值→辩护人复检", "生效"],
["final_fake_conf_threshold", "85", "终裁伪造所需最低置信度", "生效"],
["final_real_conf_threshold", "90", "终裁无伪造所需最低置信度", "生效"],
["suspicious_on_vote_split", "true", "票型分裂→存疑", "生效"],
["prior_high_threshold", "0.55", "初筛无伪造且先验>此值→控方轮", "生效"],
["prior_conflict_threshold", "0.55", "视觉无伪造+先验≥此值→存疑", "生效"],
["convict_prior", "0.70", "融合定罪先验门槛", "生效"],
["attach_event_frames", "true", "送检附加事件证据图", "生效"],
["prior_fusion", "max", "双先验融合取高值", "生效"],
["phys_guard_threshold", "0.5", "物理证据守卫：子分≥此值至少存疑", "生效"],
["route_highres", "true", "≥720P 走模型主导分支", "生效"],
["highres_min_width", "1280", "高清分支最小宽度", "生效"],
["highres_min_height", "720", "高清分支最小高度", "生效"],
["item_evidence_threshold", "3", "控方证据子分定罪/存疑阈值", "生效"],
["cv_visual_evidence", "true", "低清附加CV可视化证据图", "生效"],
["prior_anchor_table", "true", "实时先验锚定表值校正", "生效"],
["prior_convict_backstop", "0.55", "定罪背靠：伪造票定罪所需先验（0.70→0.55）", "生效"],
["highres_conflict_exempt", "false", "高清分支冲突豁免开关（v5.8 新增，取消豁免）", "生效"],
]

V58_TAIL = "五、相对 v5.7 的三处改动与预期效果"
V58_TAIL_PARAS = [
"改动一：定罪背靠 0.70 → 0.55。消融实测：校准集上同样零误报，伪造检出 31/106 → 52/106"
"（多捞回 21 条）；0.55 在外部评测集上不新增误报。",
"改动二：取消高清分支的 CV 冲突豁免（新增开关 highres_conflict_exempt=false，"
"processor.py 冲突规则同步支持，默认 true 保持旧行为）。预期：外部高清伪造中先验 ≥0.55 的漏检"
"（实测 4/16）由“无伪造”转“存疑”进入人工复核，零误报代价。",
"改动三：删除 5 项死参数（prosecutor_convict_prior、phys_guard_convict、"
"prior_fake_threshold、prior_real_threshold、band_use_votes），参数清单由 23 项减至 19 项。",
"未改动：提示词三件套、两阶段调用流程、流控参数、路由判定标准与 v5.7 完全一致。",
"验证结果（2026-09-27，100 条同批配对）：伪造检出 0 → 6（校准集 0→5、外部 0→1），真实误报 0 → 0，"
"另有 1 条外部高清伪造由“无伪造”转“存疑”。三处改动零代价全部兑现。",
]


build_doc("检测逻辑说明（v5.7 原版）", "2026-09-27 整理 | 判定策略：对称投票 + 先验路由 + 三分类",
          FLOW, VERDICT_V57, PARAMS_V57, V57_TAIL, V57_TAIL_PARAS, OUT_V57)
build_doc("检测逻辑说明（v5.8 现行版）", "2026-09-27 整理 | 判定策略：对称投票 + 先验路由 + 三分类（v5.8 简化修订）",
          FLOW, VERDICT_V58, PARAMS_V58, V58_TAIL, V58_TAIL_PARAS, OUT_V58)
