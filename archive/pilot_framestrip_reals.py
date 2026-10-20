# -*- coding: utf-8 -*-
"""① 帧条特异性检查：22 条外部高清真实，帧条+控方提示词 1 票，看是否守住"无伪造"。"""
import base64
import glob
import os
import subprocess
import sys
import time

sys.path.insert(0, r"E:\deepfake")
from src.config import AppConfig
from src.client import QwenClient
from src.processor import _parse_verdict

REAL_DIR = r"E:\deepfake\外部评测集100\real"
NAMES = [
    "01__podium_speech_happy", "01__talking_angry_couch", "01__walking_and_outside_surprised",
    "01__walking_down_street_outside_angry", "02__talking_angry_couch", "03__exit_phone_room",
    "03__walking_down_indoor_hall_disgust", "04__outside_talking_still_laughing",
    "04__podium_speech_happy", "04__talking_against_wall", "04__walking_outside_cafe_disgusted",
    "05__outside_talking_still_laughing", "06__outside_talking_pan_laughing",
    "07__outside_talking_still_laughing", "096", "11__kitchen_still", "15__exit_phone_room",
    "15__outside_talking_still_laughing", "265", "390", "410", "915",
]
FPS = 1
WORK = r"C:\Users\18500\AppData\Local\Temp\framestrip_real"

cfg = AppConfig.from_yaml(r"E:\deepfake\config_v511.yaml")
client = QwenClient(cfg)
prompt = cfg.prosecutor_prompt


def frame_strip(video_path, stem):
    os.makedirs(WORK, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", video_path, "-vf", f"fps={FPS}", "-q:v", "3",
                    os.path.join(WORK, stem + "_%03d.jpg")], check=True)
    frames = sorted(glob.glob(os.path.join(WORK, stem + "_*.jpg")))
    parts = []
    for fp in frames:
        with open(fp, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        parts.append({"type": "image_url",
                      "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    for fp in frames:
        os.remove(fp)
    return parts, len(frames)


print(f"帧条特异性检查：{len(NAMES)} 条真实 × 1 票", flush=True)
fake_votes = 0
for i, name in enumerate(NAMES, 1):
    video = os.path.join(REAL_DIR, name + ".mp4")
    if not os.path.exists(video):
        print(f"[{i}/{len(NAMES)}] {name}: 缺失，跳过", flush=True)
        continue
    try:
        parts, nframes = frame_strip(video, name)
    except Exception as e:
        print(f"[{i}/{len(NAMES)}] {name}: 抽帧失败 {e}", flush=True)
        continue
    intro = (f"【重要】以下不是视频，而是系统从视频中按每秒1帧抽取的 {nframes} 张关键帧图像，"
             f"按时间顺序排列（文件名即帧序号）。请把它们当作连续视频画面做时序分析。\n\n")
    content = [{"type": "text", "text": intro + prompt}] + parts
    try:
        resp = client._client.chat.completions.create(
            model=cfg.model, messages=[{"role": "user", "content": content}],
            max_tokens=cfg.max_tokens, temperature=cfg.temperature)
        text = resp.choices[0].message.content or ""
        vd = _parse_verdict(text)
        if vd in ("换脸", "面部重演", "全生成"):
            fake_votes += 1
        print(f"[{i}/{len(NAMES)}] {name}: 帧条={vd}  (frames={nframes})", flush=True)
    except Exception as e:
        print(f"[{i}/{len(NAMES)}] {name}: 调用失败 {str(e)[:100]}", flush=True)
    time.sleep(2)
print(f"完成：真实侧伪造票 {fake_votes}/{len(NAMES)}", flush=True)
