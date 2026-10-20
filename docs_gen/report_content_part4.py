# -*- coding: utf-8 -*-
"""报告内容 第四部分：下步优化建议、结语、参考文献。"""

SECTIONS = [
(1, '十三、下步优化调整的工作建议', [
'基于差距分析、困境清单和消融实验结论，按优先级给出八项工作建议。',
'建议一（最高优先级）：完成并验证“辩护人清账轮”（v5.10实验，进行中）。这是破解“敏感度-清白-成本不可能三角”的关键实验：在控方轮之后，对被标记样本补一轮辩护人复核，提示词附控方上一轮分析全文供逐条质证。若实验证明真实视频能被辩方翻回“无伪造”而伪造视频扛住质证，则系统可以同时获得“近零漏判+零误报+可控存疑”，这是当前所有优化中性价比最高的一步。',
'建议二：高清复检常态化启用控方提示词。v59c实验已经用数据证明：控方提示词在原始高清视频上就能把伪造漏判从19条降到1条，分辨率操作完全没有必要。建议把highres_recheck与highres_prosecutor开关在生产配置中打开（配合建议一的清账轮控制存疑），彻底废除分辨率路由的程序性豁免。',
'建议三：CV先验的系统性治理。先验是判决层的第一权重输入，但存在三类未根治问题：±0.2单次波动、来源相关偏差、分辨率相关性（低清上偏+0.114）。建议：一是用550+550全量评测集重新标定先验模型，把分辨率作为特征显式纳入而非让它成为隐藏偏差；二是对0.55冲突阈值加“迟滞带”（如0.50至0.60之间维持上轮判定），消除±0.01抖动导致的判决翻转；三是给物理证据子分补上结果存档（当前phys_score不落盘，导致离线审计无法覆盖物理守卫规则）。',
'建议四：向混合路线演进，接入专用取证工具。国际趋势（FACT取证智能体、FakeShield、ForgeryVCR）证明：大模型做推理调度+专用工具做硬测量是比纯提示词更有效的路线。本课题已有CV量化通道的雏形，建议扩展：接入频域伪影分析（FFT）、噪声指纹分析、C2PA内容凭证校验（对抗AIGC图像时有效性突出）等工具，由大模型调度、由工具出硬证据。这一方向直接对应“上游失明”困境——模型看不见的，让工具量出来。',
'建议五：550+550全量基准与持续评测机制。当前所有结论基于43至206条样本，统计功效有限。建议在550+550外部评测集上跑一次全量基准（预计约8至12小时、60至90元），建立每版配置的“成绩单”档案；同时把评测集抽样脚本、消融重放脚本固化为回归测试，以后每改一条规则自动重放历史数据检查影响。',
'建议六：多模型协同与基座对比实验。用同一套三件套提示词跑Gemini（如2.5-Pro）与千问的对照，量化“换基座”的收益；若Gemini在外部高清伪造上检出显著更高（HOLA数据暗示推理型模型有优势），可设计双模型互查机制（一票千问+一票Gemini的异质投票，用不同模型的盲区互相补位）。',
'建议七：工程加固。四项具体：修复内存问题（实验批量化运行、或换更大内存机器）；补装av库恢复唇同步量化（当前因Python 3.14无预编译包而缺失，可降级Python或源码编译）；给流水线加断点续跑（当前增量落盘但不续跑，内存被杀后浪费重复调用）；加强输出解析容错（置信度格式漂移的兜底）。',
'建议八：提示词与终裁规则对齐。提示词承诺“物理证据可单独定罪”，但终裁层的先验背靠可以否决它（历史上F45案例）——两套规则的不一致会让模型的努力白费，也让系统难以向用户解释。建议把终裁规则概要写入提示词的判定准则段，实现“说到做到”；同时对遗留的prior_high_threshold等“加载但未使用”的参数做一次代码级清理（消融实验已清掉5个死参数，尚有此类问题）。',
'八项建议的实施节奏建议：建议一、二在一周内完成（实验基础设施现成，仅需配置变更与一次43条级别的验证）；建议三、七在两周内完成（数据重标定与工程加固需要整块时间）；建议四、五、六在一个月内排期（涉及新工具接入与新模型评估，工作量较大）。每完成一项，都用同批配对验证更新系统成绩单，保持“受控实验驱动”的课题传统。',
'对每项建议再补充一句具体的启动动作，方便后续执行：建议一——运行run_defender_round.py脚本（已就绪），分析v5.10与v59c的38条对比；建议二——在config_v58.yaml基础上打开highres_recheck与highres_prosecutor开关，做一次43条级回归验证；建议三——用setup_val100h.py的选片逻辑扩展到550+550全量，重建先验标定表；建议四——以preprocessor.py的extract_cv_evidence为模板，新增频域伪影与噪声指纹两个证据图生成器；建议五——写一个全量基准驱动脚本，复用超小批次模式（每批5条）规避内存问题；建议六——client.py已抽象OpenAI兼容接口，只需新增Gemini的base_url与模型名配置即可做同提示词对照；建议七——优先做断点续跑（formatter.py已有load_incremental函数，缺的是processor层的跳过逻辑）；建议八——把终裁规则摘要写成一段提示词文本，追加进16项主提示词的判定准则段，同时删除配置中确认无引用的参数。',
]),

(1, '十四、结语', [
'回顾这三个多月的工作，本课题走完了一条完整的人工智能应用研究路径：从“一个提示词包打天下”的直觉式开发（21项版检出率0%），到用受控实验驱动每一处改动（五阶段提示词演化、八个版本判决策略、四轮消融实验链）；从把数据集偏差误认为规律（分辨率路由的教训），到用决定性实验链把每个假设证伪或证实（降清实验、v59a/b/c变量隔离）；从追求“系统更聪明”，到诚实地接受“模型的上限就是系统的上限”。',
'课题最重要的产出不是某个版本的配置，而是三样可以带走的方法论：其一，消融实验与配对实验的设计方法——怀疑任何一条规则时，先离线重放、再小样本现场、最后同批配对，用数据审判复杂度；其二，对抗式架构思想——既然单个提示词必有偏置，就让多个角色的偏置互相制衡，把“质证”而不是“投票”作为仲裁机制；其三，对模型能力的敬畏——看清边界（高清伪造失明、自信地错、思考模式无效）比堆砌技巧更重要，省下的精力应该投向工具协同和多模型互补。',
'鉴伪与伪造的对抗是一场没有终点的军备竞赛：今天的换脸检测器明天就会遇到新的生成技术。本课题系统的价值不在于“已经能挡住多少伪造”，而在于它建立了一套可以持续演进的检测框架——每一个新困境都有明确的实验手段去度量、去定位、去修复。这条路值得继续走下去。',
'最后，站在学习者的角度总结本课题最值得带走的三课。第一课：对模型的怀疑要落到数据上。怀疑系统太复杂不是凭感觉——逐个旋钮消融，让贡献为零的参数自己现形；怀疑路由设计不合理也不靠辩论——降清对照、变量隔离，让真凶自己浮出来。第二课：接受模型能力的边界，把功夫下在边界之外。提示词调优的边际收益会递减到零，CV通道、证据图、对抗架构这些“模型之外”的机制才是系统级增益的来源——这在国际学术界的混合路线趋势中得到印证。第三课：工程与科研互相成全。零成本重放之所以可能，是因为结果字段完整落盘；消融之所以可复现，是因为抽样有种子、标签有映射文件、分析有固定脚本。好的实验基础设施不是科研的附庸，而是科研结论可信度的地基。',
'站在课题收束的角度，这份报告本身也是课题的一部分：它把三个月里散落在配置注释、实验脚本、研究文档中的知识，整理成一份可供任何人接手继续工作的地图。系统中的每一处设计都能在本报告中找到它的实验依据，每一处遗留问题都能找到对应的困境描述与建议入口。如果读者只带走一句话，希望是这句：检测系统的上限由模型决定，但系统的水平由实验数据决定——把每一处怀疑变成实验，把每一个结论钉在数据上，这就是本课题的全部方法论。',
]),


(1, '十五、报告数据来源与使用说明', [
'本报告的实验数据全部来自本课题2026年6月至9月的实测记录，主要数据文件与文档保存在课题目录的output系列文件夹（各次实验的JSON结果与增量记录）与《研究文档》文件夹（历次研究文档）中。报告引用的外部基准数据来自2024至2026年公开论文与预印本，因检索获取的是论文摘要与表格片段，部分指标的确切口径（如VendorBench-100各列含义、SCEP表各数值定义）未能完全确认，引用时已尽量保守表述，凡标注“约”“据片段”之处建议读者核对原文。',
'报告中所有百分比数字的口径统一说明：检出率=检出伪造数/伪造总数；误报率=误判伪造的真实数/真实总数；存疑率=存疑数/样本总数；“综合正确率97.5%”为历史口径（硬判正确且存疑不计错，200条校准集）；外部评测集的“67%漏判”指21条高清伪造中14条被判“无伪造”的比例口径。同一系统在不同口径下会呈现不同数字，读者引用时请注意上下文。',
]),

(1, '参考文献', [
'[1] Xu et al. FakeShield: Explainable Image Forgery Detection and Localization via Multi-modal Large Language Models. ICLR 2025. https://proceedings.iclr.cc/paper_files/paper/2025/file/4d4e0ab9d8ff180bf5b95c258842d16e-Paper-Conference.pdf',
'[2] VendorBench-100: A Unified Cross-Paradigm Benchmark for Deepfake Image Detection. arXiv 2607.06254. https://arxiv-org.ezproxy.obspm.fr/html/2607.06254v1',
'[3] TriDF: Evaluating Perception, Detection, and Hallucination for Interpretable DeepFake Detection. arXiv 2512.10652. https://ar5iv.labs.arxiv.org/html/2512.10652',
'[4] MARE (FF++/Celeb-DF/多数据集对比). arXiv 2601.20433. https://browse-export.arxiv.org/pdf/2601.20433',
'[5] DeepfakeJudge / Pixels Don“t Lie (But Your Detector Might). CVPR 2026. https://www.openaccess.thecvf.com/content/CVPR2026/papers/Kuckreja_Pixels_Dont_Lie_But_Your_Detector_Might_Bootstrapping_MLLM-as-a-Judge_for_CVPR_2026_paper.pdf',
'[6] FVBench: Benchmarking Deepfake Video Detection Capability of Large Multimodal Models. CVPR 2026. https://openaccess.thecvf.com/content/CVPR2026/papers/Wang_FVBench_Benchmarking_Deepfake_Video_Detection_Capability_of_Large_Multimodal_Models_CVPR_2026_paper.pdf',
'[7] Veritas: Generalizable Deepfake Detection via Pattern-Aware Reasoning. ICML 2025. https://ar5iv.labs.arxiv.org/html/2508.21048',
'[8] HOLA: Enhancing Audio-visual Deepfake Detection via Hierarchical Contextual Aggregations. arXiv 2507.22781. https://ar5iv.labs.arxiv.org/html/2507.22781',
'[9] A Framework of Enhanced Preprocessing Techniques for Deepfake Face Verification Using Vision Language Models. IJIES 2026. https://doi.org/10.22266/ijies2026.0731.10',
'[10] FakeI2V-Bench: Benchmarking the Applicability of Image-level Deepfake Detectors for Deepfake Video Detection. arXiv 2608.03096. https://arxiv-org.ezproxy.obspm.fr/html/2608.03096v1',
'[11] ForgeryVCR: Visual-Centric Reasoning via Efficient Forensic Tools in MLLMs. AAAI 2025. https://ar5iv.labs.arxiv.org/html/2602.14098',
'[12] FACT: A Forensic Agent with Compiled Tool-Use Trajectories for AI-Generated Image Detection. arXiv 2609.05876. https://arxiv-org.ezproxy.obspm.fr/html/2609.05876v1',
'[13] Evidence Packing for Cross-Domain Image Deepfake Detection with LVLMs (SCEP). arXiv 2603.17761. https://ar5iv.labs.arxiv.org/html/2603.17761',
'[14] Foundation and Multimodal Large Language Models for Face Presentation and Morph Attack Detection. arXiv 2608.29802. https://arxiv-org.ezproxy.obspm.fr/html/2608.29802v1',
'[15] 基于视觉-语言大模型的伪造检测综述（中文）. 中国科学. https://www.sciengine.com/parse/pdf/1674-7267/A731F1D5337E4487A61C444C8FFA5CE4-mark.pdf',
'[16] 本课题内部文档：20260913_视频大模型鉴伪提示词工程调优过程回顾；20260913_鉴伪逻辑策略与决策流程及局限性分析；20260927_终裁层消融实验与v5.8配置说明（E:\\deepfake\\研究文档\\）。',
]),
]
