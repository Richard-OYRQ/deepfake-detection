"""
配置加载模块
-----------
从 YAML 配置文件读取所有设置，支持环境变量替换（${VAR_NAME}）。
自动扫描视频文件夹，发现所有视频文件并匹配提示词。
"""

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# 环境变量占位符正则：${VAR_NAME} 或 ${VAR_NAME:default_value}
_ENV_PATTERN = re.compile(r"\$\{(\w+)(?::([^}]*))?\}")

# 支持的视频扩展名
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv"}


def _resolve_env(match: re.Match) -> str:
    """替换 ${VAR} 为环境变量值，支持默认值。"""
    var_name = match.group(1)
    default = match.group(2)
    return os.environ.get(var_name, default if default is not None else match.group(0))


def _resolve_string(value: str) -> str:
    """对字符串递归替换环境变量。"""
    return _ENV_PATTERN.sub(_resolve_env, value)


def _resolve_env_vars(obj: Any) -> Any:
    """递归遍历配置对象，替换所有字符串中的环境变量。"""
    if isinstance(obj, str):
        return _resolve_string(obj)
    elif isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_vars(item) for item in obj]
    return obj


class AppConfig:
    """应用配置，提供类型安全的属性访问。"""

    def __init__(self, raw: dict):
        # --- API ---
        api = raw.get("api", {})
        self.base_url: str = api.get("base_url", "")
        self.api_key: str = api.get("api_key", "")
        self.model: str = api.get("model", "qwen-vl-plus")
        self.max_tokens: int = api.get("max_tokens", 4096)
        self.temperature: float = api.get("temperature", 0.7)
        self.timeout: int = api.get("timeout", 300)
        self.enable_thinking: bool = api.get("enable_thinking", False)
        self.fps: float | None = api.get("fps", None)

        # --- 流控 ---
        throttle = raw.get("throttle", {})
        self.max_concurrent: int = throttle.get("max_concurrent", 2)
        self.requests_per_minute: int = throttle.get("requests_per_minute", 5)
        self.retry_times: int = throttle.get("retry_times", 3)
        self.vote_count: int = throttle.get("vote_count", 1)
        self.retry_backoff: float = throttle.get("retry_backoff", 2.0)
        self.min_interval_seconds: float = throttle.get("min_interval_seconds", 2.0)
        self.recheck_temperature: float | None = throttle.get("recheck_temperature", None)

        # --- 判定策略 ---
        strategy = raw.get("strategy", {})
        self.auto_mode: bool = strategy.get("auto_mode", False)
        self.prior_fake_threshold: float = strategy.get("prior_fake_threshold", 0.60)
        self.prior_real_threshold: float = strategy.get("prior_real_threshold", 0.45)
        self.band_use_votes: bool = strategy.get("band_use_votes", True)
        self.fake_recheck_conf_threshold: int = strategy.get("fake_recheck_conf_threshold", 90)
        self.final_fake_conf_threshold: int = strategy.get("final_fake_conf_threshold", 85)
        self.final_real_conf_threshold: int = strategy.get("final_real_conf_threshold", 90)
        self.suspicious_on_vote_split: bool = strategy.get("suspicious_on_vote_split", True)
        self.prior_high_threshold: float = strategy.get("prior_high_threshold", 0.6)
        self.prior_conflict_threshold: float = strategy.get("prior_conflict_threshold", 0.7)
        self.prosecutor_convict_prior: float = strategy.get("prosecutor_convict_prior", 0.75)
        self.convict_prior: float = strategy.get("convict_prior", 0.70)
        self.defender_suffix: str = strategy.get("defender_suffix", "")
        self.prosecutor_suffix: str = strategy.get("prosecutor_suffix", "")
        self.prosecutor_prompt: str = strategy.get("prosecutor_prompt", "")
        self.attach_event_frames: bool = strategy.get("attach_event_frames", True)
        self.prior_fusion: str = strategy.get("prior_fusion", "max")
        self.phys_guard_threshold: float = strategy.get("phys_guard_threshold", 0.0)
        self.phys_guard_convict: float = strategy.get("phys_guard_convict", 0.0)
        self.item_evidence_threshold: int = strategy.get("item_evidence_threshold", 3)
        self.cv_visual_evidence: bool = strategy.get("cv_visual_evidence", True)
        self.prior_anchor_table: bool = strategy.get("prior_anchor_table", True)
        self.prior_convict_backstop: float = strategy.get("prior_convict_backstop", 0.55)
        self.lowres_real_conf_threshold: int | None = strategy.get("lowres_real_conf_threshold", None)
        # v5.11：分辨率路由已废除，路由相关参数（route_highres/highres_* 豁免与开关）全部移除

        # --- 输出 ---
        output = raw.get("output", {})
        self.output_dir: Path = Path(output.get("dir", "./output"))
        self.output_format: str = output.get("format", "json")
        self.clean_dir: bool = output.get("clean_dir", False)

        # --- 日志 ---
        logging_cfg = raw.get("logging", {})
        self.log_level: str = logging_cfg.get("level", "INFO")
        self.log_file: str = logging_cfg.get("file", "./logs/run.log")

        # --- 视频目录 & 默认提示词 ---
        videos_cfg = raw.get("videos", {})
        self.videos_dir: Path = Path(videos_cfg.get("dir", "./videos"))
        self.default_prompt: str = videos_cfg.get("prompt", "")

        # 运行时填充：由 discover_videos() 生成
        self.videos: list[dict] = []

    @property
    def video_count(self) -> int:
        return len(self.videos)

    # ------------------------------------------------------------------
    # 视频发现
    # ------------------------------------------------------------------

    def discover_videos(self) -> list[dict]:
        """
        扫描 videos_dir，自动发现所有视频文件，构建任务列表。

        提示词优先级：
        1. 与视频同名的 .txt 文件内容（如 foo.mp4 → foo.txt）
        2. 配置文件中的默认 prompt

        返回
        ----
        list[dict]
            每个元素包含 name, video_path, prompt。
        """
        if not self.videos_dir.exists():
            raise FileNotFoundError(f"视频目录不存在: {self.videos_dir.resolve()}")

        tasks = []
        found = sorted(
            f for f in self.videos_dir.iterdir()
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
        )

        if not found:
            logger.warning("视频目录 %s 中未发现视频文件", self.videos_dir.resolve())
            self.videos = []
            return []

        for video_path in found:
            name = video_path.stem  # 无扩展名的文件名
            prompt_file = video_path.with_suffix(".txt")

            if prompt_file.exists():
                prompt = prompt_file.read_text(encoding="utf-8").strip()
                logger.info("  [%s] 使用专属提示词: %s", name, prompt_file.name)
            else:
                if not self.default_prompt:
                    logger.warning("  [%s] 没有专属提示词且未配置默认 prompt，跳过", name)
                    continue
                prompt = self.default_prompt
                logger.debug("  [%s] 使用默认提示词", name)

            tasks.append({
                "name": name,
                "video_path": str(video_path.resolve()),
                "prompt": prompt,
            })

        self.videos = tasks
        logger.info("在 %s 中发现 %d 个视频", self.videos_dir.resolve(), len(tasks))
        return tasks

    # ------------------------------------------------------------------
    # 加载 & 校验
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AppConfig":
        """从 YAML 文件加载配置并解析环境变量。"""
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if raw is None:
            raise ValueError(f"配置文件为空: {path}")
        resolved = _resolve_env_vars(raw)
        return cls(resolved)

    def validate(self) -> list[str]:
        """校验配置完整性，返回错误列表。"""
        errors = []
        if not self.api_key or self.api_key.startswith("${"):
            errors.append("api_key 未设置，请在环境变量或 config.yaml 中配置")
        if not self.base_url:
            errors.append("base_url 未设置")
        if not self.model:
            errors.append("model 未设置")

        # 检查视频目录
        if not self.videos_dir.exists():
            errors.append(f"视频目录不存在: {self.videos_dir.resolve()}")

        # 检查是否有视频文件
        if self.videos_dir.exists():
            video_files = [
                f for f in self.videos_dir.iterdir()
                if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
            ]
            if not video_files:
                errors.append(f"视频目录 {self.videos_dir.resolve()} 中未发现视频文件")

        # 检查默认提示词
        if not self.default_prompt:
            has_any_prompt = False
            if self.videos_dir.exists():
                for f in self.videos_dir.iterdir():
                    if f.is_file() and f.suffix.lower() == ".txt":
                        has_any_prompt = True
                        break
            if not has_any_prompt:
                errors.append("videos.prompt 未配置，且视频目录中没有同名 .txt 提示词文件")

        return errors
