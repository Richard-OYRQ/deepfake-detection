"""
格式化输出模块
-------------
增量保存：每个视频完成后立刻写入 JSONL，中断不丢数据。
最终聚合生成 JSON + Markdown 报告。
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    for ch in forbidden:
        name = name.replace(ch, "_")
    return name.strip()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


# ==================================================================
# 增量保存（实时写入）
# ==================================================================

_incremental_path: Path | None = None


def init_incremental(output_dir: Path) -> Path:
    """初始化增量文件，返回文件路径。"""
    global _incremental_path
    output_dir.mkdir(parents=True, exist_ok=True)
    _incremental_path = output_dir / f"partial_{_now_iso()}.jsonl"
    _incremental_path.write_text("", encoding="utf-8")
    logger.info("增量结果将写入: %s", _incremental_path)
    return _incremental_path


def save_one(result: dict):
    """每完成一个视频立即追加一行 JSON。"""
    if _incremental_path is None:
        return
    with open(_incremental_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def load_incremental() -> list[dict]:
    """从增量文件读取所有已完成的结果。"""
    if _incremental_path is None or not _incremental_path.exists():
        return []
    results = []
    with open(_incremental_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


# ==================================================================
# 最终报告
# ==================================================================

def write_json(results: list[dict], output_dir: Path, run_id: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"results_{run_id}.json"

    payload = {
        "run_id": run_id,
        "generated_at": _now_iso(),
        "total": len(results),
        "succeeded": sum(1 for r in results if r.get("error") is None),
        "failed": sum(1 for r in results if r.get("error") is not None),
        "results": results,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info("JSON 结果已写入: %s", filepath)


def write_markdown(results: list[dict], output_dir: Path, run_id: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = output_dir / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "# DeepFake 视频分析报告",
        "",
        f"**生成时间**: {_now_iso()}",
        f"**总计**: {len(results)} 个视频",
        "",
        "| # | 视频 | 模型 | 状态 | 终裁 | 置信度 | tokens |",
        "|---|---|---|---|---|---|---|",
    ]

    for i, r in enumerate(results):
        name = r.get("task_name", f"task_{i}")
        safe_name = _sanitize_filename(name)
        model = r.get("model", "?")
        usage = r.get("usage") or {}
        tokens = usage.get("total_tokens", "-")
        is_ok = r.get("error") is None
        status = "OK" if is_ok else "FAIL"
        final_v = r.get("final_verdict", "-")
        final_c = r.get("final_confidence", "-")

        index_lines.append(
            f"| {i + 1} | [{name}](./{safe_name}.md) | {model} | {status} | "
            f"{final_v} | {final_c} | {tokens} |"
        )

        report_path = run_dir / f"{safe_name}.md"
        _write_single_report(report_path, r, run_id)

    index_path = run_dir / "README.md"
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    logger.info("Markdown 报告已写入: %s", run_dir)


def _write_single_report(path: Path, result: dict, run_id: str):
    name = result.get("task_name", "unknown")
    is_ok = result.get("error") is None

    lines = [
        f"# {name}",
        "",
        f"**Run ID**: `{run_id}`",
        f"**模型**: {result.get('model', '?')}",
        f"**状态**: {'OK' if is_ok else 'FAIL'}",
        f"**终裁**: {result.get('final_verdict', '-')} "
        f"(置信度 {result.get('final_confidence', '-')})",
        f"**投票**: {result.get('vote_result', '-')}",
        f"**耗时**: {result.get('elapsed_seconds', '-')}s",
        f"**重试次数**: {result.get('attempts', '-')}",
    ]

    usage = result.get("usage")
    if usage:
        lines += [
            f"**Token 用量**: prompt={usage.get('prompt_tokens', 0)}, "
            f"completion={usage.get('completion_tokens', 0)}, "
            f"total={usage.get('total_tokens', 0)}",
        ]

    if is_ok:
        lines += [
            f"**结束原因**: {result.get('finish_reason', '-')}",
            "",
            "---",
            "",
            "## 模型回答",
            "",
            result.get("content", "*（无内容）*"),
        ]
    else:
        lines += [
            "",
            "---",
            "",
            "## 错误信息",
            "",
            "```",
            result.get("error", "未知错误"),
            "```",
        ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def output_results(results: list[dict], config) -> str:
    """按配置的格式输出最终结果。返回 run_id。"""
    run_id = _now_iso()
    fmt = config.output_format.lower()
    out_dir = config.output_dir.resolve()

    if config.clean_dir and out_dir.exists():
        import shutil
        for item in out_dir.iterdir():
            p = out_dir / item.name
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
        logger.info("已清空输出目录: %s", out_dir)

    if fmt in ("json", "both"):
        write_json(results, out_dir, run_id)

    if fmt in ("markdown", "both"):
        write_markdown(results, out_dir, run_id)

    return run_id
