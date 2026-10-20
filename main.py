#!/usr/bin/env python3
"""
DeepFake 视频批量处理 —— 入口
==============================
用法:
    python main.py                        # 默认读取 config.yaml
    python main.py --config my_conf.yaml  # 指定配置文件
    python main.py --dry-run              # 仅校验配置，不实际请求
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 自动加载 .env 文件
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent
load_dotenv(_project_root / ".env")

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(_project_root))

from src.config import AppConfig
from src.client import QwenClient
from src.rate_limiter import RateLimiter
from src.processor import VideoProcessor
from src.formatter import output_results, init_incremental, save_one


def setup_logging(config: AppConfig):
    """配置日志：同时输出到控制台和文件。"""
    log_dir = Path(config.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level.upper(), logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    root_logger.addHandler(console)

    # 文件 handler
    file_handler = logging.FileHandler(config.log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    root_logger.addHandler(file_handler)

    # 降低第三方库日志噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def print_header(config: AppConfig):
    """打印启动横幅。"""
    print()
    print("=" * 56)
    print("  DeepFake 视频批量分析框架")
    print("=" * 56)
    print(f"  模型       : {config.model}")
    print(f"  API 端点   : {config.base_url}")
    print(f"  视频数量   : {config.video_count}")
    print(f"  最大并发   : {config.max_concurrent}")
    print(f"  每分钟上限 : {config.requests_per_minute}")
    print(f"  重试次数   : {config.retry_times}")
    print(f"  输出目录   : {config.output_dir.resolve()}")
    print(f"  输出格式   : {config.output_format}")
    print("-" * 56)
    print()


async def main(config_path: str, dry_run: bool = False):
    """主流程。"""
    # 1. 加载配置 & 发现视频
    cfg = AppConfig.from_yaml(config_path)
    cfg.discover_videos()

    # 2. 校验
    errors = cfg.validate()
    if errors:
        print("[ERROR] 配置校验未通过:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    # 3. 日志
    setup_logging(cfg)
    logger = logging.getLogger("main")

    # 4. 打印任务概览
    print_header(cfg)
    for i, v in enumerate(cfg.videos):
        logger.info(
            "任务 #%d: name=%s  video=%s  prompt_len=%d",
            i + 1,
            v.get("name"),
            v.get("video_path"),
            len(v.get("prompt", "")),
        )

    if dry_run:
        logger.info("--dry-run 模式下仅校验配置，跳过实际请求。")
        return

    # 4. 初始化组件
    client = QwenClient(cfg)
    limiter = RateLimiter(
        max_concurrent=cfg.max_concurrent,
        requests_per_minute=cfg.requests_per_minute,
        min_interval=cfg.min_interval_seconds,
    )
    processor = VideoProcessor(cfg, client, limiter)

    # 初始化增量保存（每个视频完成后立刻写入）
    init_incremental(cfg.output_dir)

    # 5. 执行全部任务
    start_time = datetime.now()
    results = await processor.run_all()
    elapsed = (datetime.now() - start_time).total_seconds()

    # 6. 输出结果
    run_id = output_results(results, cfg)

    # 7. 汇总
    succeeded = sum(1 for r in results if r.get("error") is None)
    logger.info("=" * 56)
    logger.info("运行完成 | run_id=%s | 总耗时 %.1fs | 成功 %d/%d",
                run_id, elapsed, succeeded, len(results))
    if succeeded < len(results):
        logger.warning("以下任务失败:")
        for r in results:
            if r.get("error"):
                logger.warning("  - %s: %s", r.get("task_name"), r.get("error"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DeepFake 视频批量处理 — 基于千问大模型"
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="配置文件路径 (默认: config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅校验配置和文件，不发起 API 请求",
    )
    args = parser.parse_args()

    asyncio.run(main(args.config, args.dry_run))
