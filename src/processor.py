"""
处理编排模块
-----------
核心调度器：遍历视频任务列表，在流控和重试策略下并发执行。

判定策略（v5.0 对称投票 + 三分类）：
- 阶段一：全部视频 1 票初筛
- 阶段二复检（3票）：
  * 初筛"无伪造" → 常规复检（原提示词）
  * 初筛"伪造"且置信度 < fake_recheck_conf_threshold → 对抗复检（辩护人提示词）
- 终裁三分类：无伪造 / 伪造 / 存疑
  * 票型分裂 → 存疑
  * 伪造但置信度 < final_fake_conf_threshold → 存疑
  * 无伪造但置信度 < final_real_conf_threshold → 存疑
"""

import asyncio
import logging
import time

import cv2
from tqdm import tqdm

from .client import QwenClient
from .formatter import save_one
from .preprocessor import (analyze_video, compute_prior, extract_cv_evidence,
                           extract_event_frames, physical_evidence_score,
                           prosecutor_evidence_score, stable_prior_probability,
                           table_prior_value)
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


def _parse_cv_verify(content: str) -> str:
    """解析面颈纹理跳变核验结论（v5.6 CV可视化证据）。"""
    import re
    m = re.search(r'面颈纹理跳变核验[：:]\s*\**\s*(支持|反对|无法判定)', content or '')
    return m.group(1) if m else ''


def _parse_verdict(content: str) -> str:
    """从模型输出中提取判定类型。"""
    if not content:
        return "unknown"
    for line in content.split('\n'):
        if '伪造类型判断' in line:
            if '无伪造' in line:
                return '无伪造'
            if '面部重演' in line:
                return '面部重演'
            if '换脸' in line:
                return '换脸'
            if '全生成' in line:
                return '全生成'
    return 'unknown'


def _parse_confidence(content: str) -> int:
    """从模型输出中提取综合置信度（容忍"合置信度"等缺字变体）。"""
    if not content:
        return 0
    import re
    m = re.search(r'置信度[：:]\s*\*{0,2}(\d+)\*{0,2}\s*/\s*100', content)
    return int(m.group(1)) if m else 0


class VideoProcessor:
    """视频批量处理器。"""

    def __init__(self, config, client: QwenClient, limiter: RateLimiter):
        self._cfg = config
        self._client = client
        self._limiter = limiter
        self._results: list[dict] = []

    # ------------------------------------------------------------------
    # 终裁
    # ------------------------------------------------------------------

    def _finalize_result(self, r: dict, prior_p: float | None = None,
                         phys_score: float | None = None,
                         highres: bool = False) -> dict:
        """
        终裁。两种模式（config strategy.auto_mode）：

        【全自动模式】无人工复核，CV 先验为主判决器：
          prior ≥ prior_fake_threshold → 伪造
          prior < prior_real_threshold → 无伪造
          边界带 [prior_real_threshold, prior_fake_threshold)：
            模型有 ≥1 伪造票 → 伪造，否则 → 无伪造
          物理证据守卫：phys_score ≥ phys_guard_convict 且先验不低于真实阈值 → 伪造
          （先验不可用时的退路：沿用三分类规则）

        【三分类模式】无伪造 / 伪造 / 存疑：
          存疑触发：票型分裂 / 置信度不足 / 视觉无伪造但先验偏高（冲突，交人工复核）
            / 物理证据守卫（phys_score ≥ phys_guard_threshold，物理不可能性伪影）
          伪造定罪：任一伪造票 ∧ 先验 ≥ convict_prior（B方案融合规则）
        """
        if r.get("error") is not None:
            r["final_verdict"] = "失败"
            r["final_confidence"] = 0
            return r

        verdict = _parse_verdict(r.get("content", ""))
        conf = _parse_confidence(r.get("content", ""))
        tally = r.get("vote_result")

        # ---- 全自动模式：先验主判 + 边界带模型票 ----
        # 高清分支：模型票主导（先验阈值不参与）
        if getattr(self._cfg, 'auto_mode', False) and highres and tally is not None:
            fake_votes = sum(tally.get(k, 0) for k in ('换脸', '面部重演', '全生成'))
            if fake_votes >= 1:
                r["final_verdict"] = "伪造" if conf >= self._cfg.final_fake_conf_threshold else "存疑"
            else:
                r["final_verdict"] = "无伪造" if conf >= self._cfg.final_real_conf_threshold else "存疑"
            r["final_confidence"] = conf
            return r

        if getattr(self._cfg, 'auto_mode', False) and prior_p is not None:
            fake_thr = getattr(self._cfg, 'prior_fake_threshold', 0.60)
            real_thr = getattr(self._cfg, 'prior_real_threshold', 0.45)
            if prior_p >= fake_thr:
                r["final_verdict"] = "伪造"
            elif not highres and r.get("evidence_score", 0) \
                    >= getattr(self._cfg, 'item_evidence_threshold', 3):
                # 控方证据子分定罪（v5.5）：模型逐项证据表≥3个分离性异常 → 伪造
                r["final_verdict"] = "伪造"
            elif phys_score is not None \
                    and phys_score >= getattr(self._cfg, 'phys_guard_convict', 0.0) > 0 \
                    and prior_p >= real_thr:
                # 物理证据守卫：先验不足但物理不可能性伪影极端 → 伪造
                r["final_verdict"] = "伪造"
            elif prior_p < real_thr:
                r["final_verdict"] = "无伪造"
            elif getattr(self._cfg, 'band_use_votes', True) and tally is not None:
                fake_votes = sum(tally.get(k, 0) for k in ('换脸', '面部重演', '全生成'))
                r["final_verdict"] = "伪造" if fake_votes >= 1 else "无伪造"
            else:
                r["final_verdict"] = "无伪造"
            r["final_confidence"] = conf
            return r

        # ---- 三分类模式 ----
        # 零信号守卫（v5.12）：先验或 phys 缺失（特征管线失效）时不得硬判任何方向，
        # 一律存疑交人工复核——此前缺失样本静默走"无伪造"（self160 的 F63/F74/F88/F96 全漏）
        if prior_p is None or phys_score is None:
            r["final_verdict"] = "存疑"
            r["final_confidence"] = conf
            r["no_signal_guard"] = True
            return r

        # 融合定罪规则（B方案）：复检轮任一伪造票 + CV 先验 ≥ convict_prior → 硬判"伪造"
        # 控方轮（prosecutor_round）的伪造票只进存疑、不参与定罪——
        # v5.11 首跑（全量100条）证实该条款是零误报守门员：删除后高先验真实
        # 3 条被误定罪；v5.11 修正版恢复此条款（检出回落由人工复核兜底）
        if tally is not None:
            fake_votes = sum(tally.get(k, 0) for k in ('换脸', '面部重演', '全生成'))
            if fake_votes >= 1 and prior_p is not None \
                    and prior_p >= getattr(self._cfg, 'convict_prior', 0.70):
                if r.get('prosecutor_round'):
                    r["final_verdict"] = "存疑"
                    r["final_confidence"] = conf
                    return r
                r["final_verdict"] = "伪造"
                r["final_confidence"] = conf
                return r

        # 票型分裂 → 存疑（保守处理，交给人工复核）
        if tally and len(tally) > 1 and getattr(self._cfg, 'suspicious_on_vote_split', True):
            r["final_verdict"] = "存疑"
            r["final_confidence"] = conf
            return r

        # 视觉"无伪造" vs CV 先验偏高 → 冲突 → 存疑（v5.11：全员适用，路由豁免已废除）
        if verdict == "无伪造" and prior_p is not None \
                and prior_p >= getattr(self._cfg, 'prior_conflict_threshold', 0.7):
            r["final_verdict"] = "存疑"
            r["final_confidence"] = conf
            return r

        # 物理证据守卫：先验不足但物理不可能性伪影极端 → 存疑（v5.11：全员适用）
        if verdict == "无伪造" and phys_score is not None \
                and phys_score >= getattr(self._cfg, 'phys_guard_threshold', 0.0) > 0:
            r["final_verdict"] = "存疑"
            r["final_confidence"] = conf
            r["phys_guard"] = True
            return r

        # 控方证据子分：模型逐项证据表≥阈值 → 存疑（兜底；正常路径已由控方票覆盖）
        if verdict == "无伪造" \
                and r.get("evidence_score", 0) >= getattr(self._cfg, 'item_evidence_threshold', 3):
            r["final_verdict"] = "存疑"
            r["final_confidence"] = conf
            return r

        # CV可视化核验（v5.6）：被证据图锚定后模型确认"面颈纹理跳变" → 存疑
        # （配对实验：敏感~45%/特异~93%，不足以定罪，作为安全证据线索）
        if verdict == "无伪造" \
                and _parse_cv_verify(r.get("content", "")) == '支持':
            r["final_verdict"] = "存疑"
            r["final_confidence"] = conf
            r["cv_verify"] = "支持"
            return r

        if verdict == "无伪造":
            # v5.12：低清样本判"无伪造"可要求更高置信度（豆包方案同款思路，
            # 低清压缩噪声干扰大，默认 None=与高清同门槛）
            real_thr = self._cfg.final_real_conf_threshold
            lr_thr = getattr(self._cfg, 'lowres_real_conf_threshold', None)
            if lr_thr and not highres:
                real_thr = max(real_thr, lr_thr)
            r["final_verdict"] = "无伪造" if conf >= real_thr else "存疑"
        elif verdict in ("换脸", "面部重演", "全生成"):
            # v5.7：伪造票定罪需先验背书（backstop），否则降级存疑
            # （官方实跑：保守票对低先验真实偶发高置信定罪，如84.mp4）
            # v5.11 修正：控方轮票型无论多一致均不定罪（v5.11 首跑实证：
            # 控方轮一致票定罪在真实视频上 1/9 误报，且与真伪造在全部特征上不可分）
            if conf >= self._cfg.final_fake_conf_threshold and prior_p is not None \
                    and prior_p >= getattr(self._cfg, 'prior_convict_backstop', 0.55) \
                    and not r.get('prosecutor_round'):
                r["final_verdict"] = "伪造"
            else:
                r["final_verdict"] = "存疑"
        else:
            r["final_verdict"] = "存疑"
        r["final_confidence"] = conf
        return r

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    async def run_all(self) -> list[dict]:
        """执行所有视频任务（两阶段：1票初筛 + 对称3票复检）。"""
        tasks = self._cfg.videos
        if not tasks:
            logger.warning("没有待处理的视频任务")
            return []

        vote_count = getattr(self._cfg, 'vote_count', 1)
        logger.info("开始处理 %d 个视频，最大并发=%d，RPM=%.1f，策略=%d票",
                     len(tasks), self._cfg.max_concurrent, self._cfg.requests_per_minute, vote_count)

        # ---- 阶段一：全部 1 票初筛 ----
        logger.info("=== 阶段一：1票初筛 (%d 个视频) ===", len(tasks))
        stage1_results = await self._run_batch(tasks, vote_count=1, desc="阶段一 初筛")

        # ---- 分类：哪些需要复检 ----
        name_to_task = {t.get("name"): t for t in tasks}
        recheck_real = []   # 初筛"无伪造" → 常规复检
        recheck_fake = []   # 初筛"伪造"但置信度不足 → 对抗复检
        passed = []
        for r in stage1_results:
            if r.get("error") is not None:
                passed.append(r)
                continue
            verdict = _parse_verdict(r.get("content", ""))
            conf = _parse_confidence(r.get("content", ""))
            if verdict == "无伪造":
                recheck_real.append(r)
            elif verdict in ("换脸", "面部重演", "全生成") \
                    and conf < getattr(self._cfg, 'fake_recheck_conf_threshold', 90):
                recheck_fake.append(r)
            else:
                passed.append(r)

        logger.info("阶段一完成：直接通过 %d，无伪造需复检 %d，伪造需对抗复检 %d",
                     len(passed), len(recheck_real), len(recheck_fake))

        replacements = {}  # task_name -> 复检结果

        # ---- 阶段二A：对"无伪造"视频 3 票复检 ----
        # v5.11 统一流程：全部视频一律控方对抗复核（v59c 实证：控方提示词在
        # 高清上把伪造漏判 19→1；分辨率路由已废除，不再有分支差异）
        if recheck_real and vote_count >= 2:
            prosecutor_prompt = getattr(self._cfg, 'prosecutor_prompt', '')
            recheck_tasks = []
            for r in recheck_real:
                t = name_to_task.get(r.get("task_name"))
                if not t:
                    continue
                if prosecutor_prompt:
                    recheck_tasks.append(dict(t, prompt=prosecutor_prompt,
                                              prosecutor_round=True))
                else:
                    recheck_tasks.append(t)
            # v5.12 温度分层：复检轮可配置极低温度（抑制票型噪声与输出漂移）
            r_temp = getattr(self._cfg, 'recheck_temperature', None)
            if r_temp is not None:
                for t in recheck_tasks:
                    t["temperature"] = r_temp
            logger.info("=== 阶段二A：无伪造 3票复检 (%d 个视频，控方对抗%s) ===",
                         len(recheck_tasks), f"，温度{r_temp}" if r_temp is not None else "")
            if recheck_tasks:
                stage2_results = await self._run_batch(recheck_tasks, vote_count=3, desc="阶段二A 复检")
                for r in stage2_results:
                    if r.get("error") is None:
                        # 控方证据子分：从逐项证据表提取（模型逐项观察的量化信号）
                        r["evidence_score"] = prosecutor_evidence_score(r.get("content", ""))
                        replacements[r.get("task_name")] = r

        # ---- 阶段二B：对低置信度"伪造"视频 3 票对抗复检（辩护人）----
        if recheck_fake and vote_count >= 2:
            logger.info("=== 阶段二B：伪造对抗复检 (%d 个视频) ===", len(recheck_fake))
            defender_suffix = getattr(self._cfg, 'defender_suffix', "")
            recheck_tasks = []
            for r in recheck_fake:
                t = name_to_task.get(r.get("task_name"))
                if t:
                    # 辩护人提示词追加到原提示词末尾（预处理报告仍由 _process_one 注入）
                    recheck_tasks.append(dict(
                        t, prompt=t.get("prompt", "") + "\n\n" + defender_suffix))
            if recheck_tasks:
                stage2_results = await self._run_batch(recheck_tasks, vote_count=3, desc="阶段二B 对抗复检")
                for r in stage2_results:
                    if r.get("error") is None:
                        replacements[r.get("task_name")] = r

        # ---- 合并结果 ----
        stage1_by_name = {r.get("task_name"): r for r in stage1_results}
        for name, r in replacements.items():
            stage1_by_name[name] = r
        stage1_results = list(stage1_by_name.values())

        # ---- 终裁：三分类（带 CV 先验冲突检测 + 物理证据守卫 + 自适应路由）----
        self._results = []
        for r in stage1_results:
            t = name_to_task.get(r.get("task_name"), {})
            prior_p = t.get("prior_p")
            final = self._finalize_result(r, prior_p, t.get("phys_score"),
                                          bool(t.get("highres", False)))
            if prior_p is not None:
                final["prior_p"] = round(prior_p, 3)  # 写入结果，供评估与融合使用
            if t.get("highres"):
                final["highres"] = True
            if t.get("phys_score") is not None:
                final["phys_score"] = round(t.get("phys_score"), 3)  # v5.11：落盘供离线审计
            self._results.append(final)
        verdict_counts = {}
        for r in self._results:
            fv = r.get("final_verdict", "?")
            verdict_counts[fv] = verdict_counts.get(fv, 0) + 1
        logger.info("全部处理完成：%s", dict(verdict_counts))
        return self._results

    async def _run_batch(self, tasks: list[dict], vote_count: int, desc: str) -> list[dict]:
        """执行一批视频任务。"""
        pbar = tqdm(total=len(tasks), desc=desc, unit="视频")

        async def _tracked(index: int, task: dict) -> dict:
            try:
                result = await self._process_one(index, task, override_votes=vote_count)
            except Exception as e:
                result = {
                    "task_name": task.get("name", f"task_{index}"),
                    "model": task.get("model", self._cfg.model),
                    "content": "",
                    "usage": None,
                    "finish_reason": "error",
                    "error": str(e),
                    "elapsed_seconds": 0,
                    "attempts": 0,
                }
            task_name = result.get("task_name", "?")
            if result.get("error") is None:
                pbar.set_postfix_str(f"✅ {task_name}")
            else:
                pbar.set_postfix_str(f"❌ {task_name}")
            pbar.update(1)
            save_one(result)
            return result

        coros = [_tracked(i, task) for i, task in enumerate(tasks)]
        results = list(await asyncio.gather(*coros))
        pbar.close()
        return results

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _process_one(self, index: int, task: dict, override_votes: int = 0) -> dict:
        """处理单个视频，含重试逻辑 + 多次投票。"""
        task_name = task.get("name", f"task_{index}")
        max_retries = self._cfg.retry_times
        vote_count = override_votes if override_votes > 0 else getattr(self._cfg, 'vote_count', 1)

        # ---- 预处理：面部清晰度量化检测（仅执行一次）----
        video_path = task.get("video_path", "")
        preprocess_report = ""
        # v5.11：分辨率仅作为特征记录（供先验模型与分析使用），不再参与流程分支
        if "highres" not in task:
            task["highres"] = False
            if video_path:
                try:
                    probe = cv2.VideoCapture(video_path)
                    w = int(probe.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    probe.release()
                    task["highres"] = (w >= 1280 and h >= 720)
                except Exception:
                    pass
        if video_path:
            try:
                logger.info("[%s] 预处理: 面部清晰度量化分析 ...", task_name)
                pre_result = await asyncio.to_thread(analyze_video, video_path)
                summary = pre_result.get("summary", "")
                if not summary:
                    # v5.12：解码/检测存在非确定性，零信号先重跑一次再放弃
                    # （后补算实验：6 条零信号样本重跑后 5 条恢复 prior/phys）
                    logger.warning("[%s] 预处理未检出人脸，重试一次 ...", task_name)
                    pre_result = await asyncio.to_thread(analyze_video, video_path)
                    summary = pre_result.get("summary", "")
                if summary:
                    preprocess_report = "\n\n" + summary
                    # 稳定先验（缓存+中位数+双先验融合）：路由、注入与终裁统一使用同一数值
                    p = await asyncio.to_thread(
                        stable_prior_probability, video_path, pre_result,
                        fusion=getattr(self._cfg, 'prior_fusion', 'max'))
                    if p is not None:
                        task["prior_p"] = p
                    # v5.7：实时先验锚定表值（官方实跑发现实时先验系统性上偏，表值更稳定）
                    if getattr(self._cfg, 'prior_anchor_table', False):
                        anchored = table_prior_value(video_path)
                        if anchored is not None and p is not None and abs(anchored - p) > 0.15:
                            logger.info("[%s] 先验锚定: 实时%.2f → 表值%.2f", task_name, p, anchored)
                            p = anchored
                    prior = compute_prior(pre_result, p_override=p)
                    if prior:
                        preprocess_report += prior
                    # 物理证据子分（守卫规则用）
                    phys = physical_evidence_score(pre_result)
                    if phys is not None:
                        task["phys_score"] = phys
                    logger.info("[%s] 预处理报告已注入 (prior=%.2f, phys=%.2f)",
                                task_name, task.get("prior_p", -1.0),
                                task.get("phys_score", float('nan')))
                else:
                    # 失败必须可见：零信号视频会缺失 prior/phys，直接影响融合与终裁
                    logger.warning("[%s] 预处理未检出人脸，先验/phys 跳过（%s）",
                                   task_name, pre_result.get("error") or "无摘要")
            except Exception as e:
                logger.warning("[%s] 预处理异常: %s", task_name, str(e))

        # ---- 补充证据图（转动/遮挡事件帧 + CV可视化证据，仅提取一次，跨投票复用）----
        if "extra_images" not in task and video_path:
            try:
                events = await asyncio.to_thread(extract_event_frames, video_path)
                task["extra_images"] = events
                if events:
                    logger.info("[%s] 提取补充证据图 %d 张", task_name, len(events))
                # CV 可视化证据（v5.11）：纹理热力图+面颈剖面，全员附加
                # （v59b 实证：高清附加 CV 图 +2 伪造转存疑、真实零代价）
                if getattr(self._cfg, 'cv_visual_evidence', True):
                    cv_ev = await asyncio.to_thread(extract_cv_evidence, video_path)
                    task["extra_images"] = task["extra_images"] + cv_ev
                    if cv_ev:
                        logger.info("[%s] 提取CV证据图 %d 张", task_name, len(cv_ev))
            except Exception as e:
                task["extra_images"] = []
                logger.warning("[%s] 补充证据图提取异常: %s", task_name, str(e))
        extra_images = task.get("extra_images") or []

        original_prompt = task.get("prompt", "")
        augmented_task = dict(task)
        augmented_task["extra_images"] = extra_images
        if extra_images:
            parts = [f"图{i}: {ev.get('label', '')} (t={ev.get('ts', 0):.1f}s)"
                     for i, ev in enumerate(extra_images, 1)]
            original_prompt += (
                "\n\n【补充证据图】系统额外提供了 %d 张关键帧图像（按下方顺序）：\n  "
                % len(extra_images)
                + "\n  ".join(parts)
                + "\n检查遮挡物与人脸交界的完整性、以及头部转动过程中面部几何的连续性时，"
                  "请优先在这些放大/序列/帧差增强图中寻找证据。帧差增强图中相邻帧差异已放大，"
                  "几何抖动与闪烁表现为边缘处的杂乱高亮；转动序列图为同一脸部区域的连续帧并排，"
                  "请跨帧对比五官位置与形状的连续性。"
            )
        if any('CV证据图' in ev.get('label', '') for ev in extra_images):
            original_prompt += (
                "\n\n【CV证据图核验】另有两张CV测量可视化图（纹理密度热力图：绿框=人脸/红框=颈部，"
                "暖色=纹理细节多/冷色=平滑；面颈清晰度剖面：绿线=面颈分界，左面部/右颈部）。"
                "现代换脸的典型痕迹是\"面部软化\"——换脸重绘使面部纹理细节明显少于颈部。"
                "请结合证据图完成一项附加核验：视频中面颈交界处是否存在可见的纹理密度跳变"
                "（面部一侧明显更平滑）？在\"综合评估\"部分末尾增加一行：\n"
                "- 面颈纹理跳变核验：支持 / 反对 / 无法判定（附一句理由）"
            )
        augmented_task["prompt"] = original_prompt + preprocess_report

        # ---- 辅助：单次API调用 ----
        async def _single_call(attempt_label: str) -> dict | None:
            for attempt in range(1, max_retries + 1):
                try:
                    logger.debug("[%s] %s attempt %d/%d ...", task_name, attempt_label, attempt, max_retries)
                    await self._limiter.acquire()
                    start = time.monotonic()
                    result = await asyncio.to_thread(self._client.call, augmented_task)
                    elapsed = time.monotonic() - start
                    self._limiter.release()

                    if result.get("error") is None:
                        result["elapsed_seconds"] = round(elapsed, 1)
                        result["attempts"] = attempt
                        return result

                    logger.warning("[%s] %s 第 %d 次失败: %s", task_name, attempt_label, attempt, result["error"])
                    if attempt < max_retries:
                        await asyncio.sleep(self._cfg.retry_backoff ** attempt)
                except Exception as e:
                    logger.error("[%s] %s 第 %d 次异常: %s", task_name, attempt_label, attempt, str(e))
                    self._limiter.release()
                    if attempt < max_retries:
                        await asyncio.sleep(self._cfg.retry_backoff ** attempt)
            return None

        # ---- 多次投票 ----
        votes = []
        for v in range(vote_count):
            label = f"vote{v+1}/{vote_count}" if vote_count > 1 else "call"
            result = await _single_call(label)
            if result:
                votes.append(result)
                logger.info("[%s] %s 完成, tokens=%s", task_name, label, result["usage"]["total_tokens"])
            else:
                logger.error("[%s] %s 全部重试耗尽", task_name, label)

        if not votes:
            logger.error("[%s] 所有投票均失败", task_name)
            return {
                "task_name": task_name,
                "model": task.get("model", self._cfg.model),
                "content": "",
                "usage": None,
                "finish_reason": "exhausted",
                "error": f"投票 {vote_count} 轮全部失败",
                "elapsed_seconds": 0,
                "attempts": max_retries,
            }

        if len(votes) == 1:
            votes[0]['prosecutor_round'] = bool(task.get('prosecutor_round', False))
            return votes[0]

        # ---- 多数投票 ----
        def _parse_verdict(content: str) -> str:
            """从模型输出中提取判定类型。"""
            for line in content.split('\n'):
                if '伪造类型判断' in line:
                    if '无伪造' in line: return '无伪造'
                    if '面部重演' in line: return '面部重演'
                    if '换脸' in line: return '换脸'
                    if '全生成' in line: return '全生成'
            return 'unknown'

        def _parse_confidence(content: str) -> int:
            import re
            m = re.search(r'置信度[：:]\s*\*{0,2}(\d+)\*{0,2}\s*/\s*100', content)
            return int(m.group(1)) if m else 0

        verdicts = [_parse_verdict(v['content']) for v in votes]
        from collections import Counter
        tally = Counter(verdicts)
        most_common = tally.most_common()

        logger.info("[%s] 投票结果: %s", task_name, dict(tally))

        if len(most_common) == 1 or most_common[0][1] > most_common[1][1]:
            winner_verdict = most_common[0][0]
        else:
            # 平票：选置信度最高的
            winner_verdict = max(
                [v for v in votes if _parse_verdict(v['content']) in [mc[0] for mc in most_common]],
                key=lambda v: _parse_confidence(v['content'])
            )
            winner_verdict = _parse_verdict(winner_verdict['content'])

        winner = max(
            [v for v in votes if _parse_verdict(v['content']) == winner_verdict],
            key=lambda v: _parse_confidence(v['content'])
        )
        # 标记投票信息
        winner['vote_result'] = dict(tally)
        winner['vote_count'] = vote_count
        winner['prosecutor_round'] = bool(task.get('prosecutor_round', False))
        return winner
