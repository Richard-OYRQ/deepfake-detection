"""
API 客户端模块
-------------
统一使用 OpenAI 兼容 API。视频来源：
1. 已有 video_url → 直接引用
2. 本地小文件 → base64 内联
3. 本地大文件 → 上传 DashScope → 查签名 URL → 引用
"""

import base64
import logging
import mimetypes
from pathlib import Path

import cv2
import requests
from openai import OpenAI

logger = logging.getLogger(__name__)

VIDEO_MIME_MAP = {
    ".mp4": "video/mp4", ".avi": "video/avi", ".mkv": "video/x-matroska",
    ".mov": "video/quicktime", ".webm": "video/webm", ".flv": "video/x-flv",
    ".wmv": "video/x-ms-wmv",
}

# 小于此值走 base64。
# 注意：DashScope 限制单个 data-uri 最大 20 MiB（20971520 字节），base64 编码膨胀 4/3，
# 因此原始文件需 ≤ 15 MiB 才安全（15×4/3=20MiB）；更大文件走上传签名 URL。
# （2026-08-26 修复：15.mp4 原始 16.8MB 走 base64 被 400 拒绝，与 8/23 全量失败同因）
BASE64_THRESHOLD_BYTES = 15 * 1024 * 1024  # 15 MiB

# DashScope 原生 API
FILE_API = "https://dashscope.aliyuncs.com/api/v1/files"

# URL 缓存: video_path → signed_url
_url_cache: dict[str, str] = {}


def _guess_mime(path: str) -> str:
    ext = Path(path).suffix.lower()
    return VIDEO_MIME_MAP.get(ext, mimetypes.guess_type(path)[0] or "video/mp4")


class QwenClient:
    """千问大模型 OpenAI 兼容客户端。"""

    def __init__(self, config):
        self._cfg = config
        self._api_key = config.api_key
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    # ==================================================================
    # 大文件：上传 + 获取签名 URL
    # ==================================================================

    def _get_signed_url(self, video_path: str) -> str:
        """
        上传视频到 DashScope 并获取带签名的 OSS URL。
        该 URL 可直接在 OpenAI 兼容 API 中使用。
        """
        if video_path in _url_cache:
            return _url_cache[video_path]

        path = Path(video_path)
        size_mb = path.stat().st_size / (1024 * 1024)
        mime = _guess_mime(video_path)

        # Step 1: 上传
        logger.info("  [上传] %s (%.1f MB) ...", path.name, size_mb)

        resp = requests.post(
            FILE_API,
            files={"file": (path.name, open(video_path, "rb"), mime)},
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=120,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"上传失败 HTTP {resp.status_code}: {resp.text[:300]}")

        uploaded = resp.json().get("data", {}).get("uploaded_files", [])
        if not uploaded:
            raise RuntimeError(f"上传返回异常: {resp.json()}")
        file_id = uploaded[0]["file_id"]

        # Step 2: 查询元数据获取签名 URL
        meta_resp = requests.get(
            f"{FILE_API}/{file_id}",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=30,
        )
        if meta_resp.status_code != 200:
            raise RuntimeError(f"查询文件元数据失败 HTTP {meta_resp.status_code}")

        url = meta_resp.json().get("data", {}).get("url", "")
        if not url:
            raise RuntimeError(f"未找到 URL: {meta_resp.json()}")

        logger.info("  [就绪] %s", url[:80] + "...")
        _url_cache[video_path] = url
        return url

    # ==================================================================
    # 小文件：base64 编码
    # ==================================================================

    def _encode_base64(self, video_path: str) -> str:
        path = Path(video_path)
        mime = _guess_mime(video_path)
        with open(video_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{data}"

    # ==================================================================
    # 统一调用（兼容 API）
    # ==================================================================

    def _call_api(self, task_name: str, video_url: str, prompt: str,
                  model: str, max_tokens: int,
                  extra_images: list | None = None,
                  temperature: float | None = None) -> dict:
        """OpenAI 兼容 API 调用（视频 + 可选补充证据图 + 提示词混装）。
        api.fps 可选：控制模型内部抽帧密度（DashScope 视频参数，默认不传）。
        temperature 可选：按任务覆盖全局温度（v5.12 温度分层：复检轮极低温度）。"""
        video_part = {"url": video_url}
        if getattr(self._cfg, 'fps', None):
            video_part["fps"] = self._cfg.fps
        content = [{"type": "video_url", "video_url": video_part}]
        for data_url in (extra_images or []):
            content.append({"type": "image_url", "image_url": {"url": data_url}})
        content.append({"type": "text", "text": prompt})
        messages = [{"role": "user", "content": content}]

        logger.info(">>> [%s] 请求 %s ...", task_name, model)

        kwargs = dict(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature if temperature is not None else self._cfg.temperature,
        )
        if getattr(self._cfg, 'enable_thinking', False):
            # qwen3-vl-plus 混合思考模式（DashScope 兼容参数）
            kwargs["extra_body"] = {"enable_thinking": True}
        resp = self._client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        return {
            "task_name": task_name,
            "model": resp.model,
            "content": choice.message.content or "",
            "usage": {
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "total_tokens": resp.usage.total_tokens if resp.usage else 0,
            },
            "finish_reason": choice.finish_reason or "unknown",
            "error": None,
        }

    # ==================================================================
    # 入口
    # ==================================================================

    def _encode_image_base64(self, image_bgr) -> str | None:
        """将 BGR 图像编码为 JPEG data URL（补充证据图用）。"""
        ok, buf = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not ok:
            return None
        return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")

    def call(self, task: dict) -> dict:
        """执行单次视频问答（可携带补充证据图）。"""
        task_name = task.get("name", "unknown")
        video_path = task.get("video_path", "")
        video_url = task.get("video_url", "")
        prompt = task.get("prompt", "")
        model = task.get("model", self._cfg.model)
        max_tokens = task.get("max_tokens", self._cfg.max_tokens)
        temperature = task.get("temperature")

        extra_data_urls = []
        for item in (task.get("extra_images") or []):
            img = item.get("image")
            if img is not None:
                url = self._encode_image_base64(img)
                if url:
                    extra_data_urls.append(url)
        if extra_data_urls:
            logger.debug("  [%s] 附加证据图 %d 张", task_name, len(extra_data_urls))

        def _err(msg):
            return {"task_name": task_name, "model": model, "content": "",
                    "usage": None, "finish_reason": "error", "error": msg}

        # --- 策略 1: 已有 URL ---
        if video_url:
            try:
                result = self._call_api(task_name, video_url, prompt, model, max_tokens,
                                        extra_data_urls, temperature)
                logger.info("<<< [%s] 完成, tokens=%s",
                            task_name, result["usage"]["total_tokens"])
                return result
            except Exception as e:
                return _err(str(e))

        # --- 策略 2: 小文件 base64 ---
        path = Path(video_path)
        size_mb = path.stat().st_size / (1024 * 1024)

        if path.stat().st_size <= BASE64_THRESHOLD_BYTES:
            try:
                url = self._encode_base64(video_path)
                logger.debug("  [%s] %.1f MB, base64", task_name, size_mb)
                result = self._call_api(task_name, url, prompt, model, max_tokens,
                                        extra_data_urls, temperature)
                logger.info("<<< [%s] 完成, tokens=%s",
                            task_name, result["usage"]["total_tokens"])
                return result
            except Exception as e:
                return _err(str(e))

        # --- 策略 3: 大文件 → 上传 → 签名 URL ---
        try:
            url = self._get_signed_url(video_path)
            result = self._call_api(task_name, url, prompt, model, max_tokens,
                                    extra_data_urls, temperature)
            logger.info("<<< [%s] 完成, tokens=%s",
                        task_name, result["usage"]["total_tokens"])
            return result
        except Exception as e:
            return _err(str(e))
