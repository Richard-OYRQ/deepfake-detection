# -*- coding: utf-8 -*-
"""① fps 实验受控版：帧条试点。
对 21 条外部高清伪造，抽每秒 1 帧（带时间戳）当图片送控方提示词，1 票，
与 v5.11 的"整段视频"结果对比——检验"采样密度"是否影响模型判断。
"""
import base64
import glob
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, r"E:\deepfake")
from src.config import AppConfig
from src.client import QwenClient
from src.processor import _parse_verdict

# 21 条外部高清伪造（原片路径）
FAKE_DIR = r"E:\deepfake\外部评测集100\fake"
NAMES = [
    "01_21__walk_down_hall_angry__03X7CELV", "02_15__outside_talking_pan_laughing__SB6PMCO0",
    "03_07__walking_down_indoor_hall_disgust__PWXXULHR", "04_07__exit_phone_room__ITC0C48B",
    "04_18__kitchen_still__NAXINA1N", "05_08__talking_against_wall__PRBCE28Z",
    "06_02__walk_down_hall_angry__37DH75GQ", "06_14__outside_talking_pan_laughing__8U9ULZDT",
    "07_03__outside_talking_pan_laughing__IFSURI9X", "07_25__walk_down_hall_angry__PAE9HCA8",
    "10_19__kitchen_still__IDX76N5R", "Deepfakes_805_011", "Face2Face_286_267",
    "Face2Face_362_354", "Face2Face_851_552", "FaceShifter_688_645", "FaceSwap_162_330",
    "FaceSwap_818_820", "NeuralTextures_633_529", "NeuralTextures_796_740", "NeuralTextures_943_942",
]
FPS = 1
WORK = r"C:\Users\18500\AppData\Local\Temp\framestrip"

cfg = AppConfig.from_yaml(r"E:\deepfake\config_v511.yaml")
client = QwenClient(cfg)
prompt = cfg.prosecutor_prompt

# v5.11 已有结果（对照）
v511 = {}
for f in sorted(glob.glob(r"E:\deepfake\output_v511_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        n = r["task_name"][:-4] if r["task_name"].endswith(".mp4") else r["task_name"]
        v511["E_fake_" + n] = r if n in NAMES else v511.get("E_fake_" + n, r)
# 修正：v511 结果里的名字是 E_fake_ 前缀
v511 = {}
for f in sorted(glob.glob(r"E:\deepfake\output_v511_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        n = r["task_name"][:-4] if r["task_name"].endswith(".mp4") else r["task_name"]
        v511[n] = r


def frame_strip(video_path):
    """ffmpeg 抽每秒1帧 → JPEG base64 列表（带时间戳说明）。"""
    os.makedirs(WORK, exist_ok=True)
    stem = os.path.splitext(os.path.basename(video_path))[0]
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", video_path, "-vf", f"fps={FPS}", "-q:v", "3",
                    os.path.join(WORK, stem + "_%03d.jpg")], check=True)
    frames = sorted(glob.glob(os.path.join(WORK, stem + "_*.jpg")))
    parts = []
    for i, fp in enumerate(frames):
        with open(fp, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        parts.append({"type": "image_url",
                      "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    for fp in frames:
        os.remove(fp)
    return parts, len(frames)


print(f"帧条试点：{len(NAMES)} 条 × 1 票（fps={FPS}，控方提示词）", flush=True)
for i, name in enumerate(NAMES, 1):
    video = os.path.join(FAKE_DIR, name + ".mp4")
    if not os.path.exists(video):
        print(f"[{i}/{len(NAMES)}] {name}: 原片缺失，跳过", flush=True)
        continue
    try:
        parts, nframes = frame_strip(video)
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
        old = v511.get("E_fake_" + name, {}).get("final_verdict", "?")
        mark = "  <-- 变化" if vd != old else ""
        print(f"[{i}/{len(NAMES)}] {name}: 帧条={vd}  视频版={old}{mark}  (frames={nframes})", flush=True)
    except Exception as e:
        print(f"[{i}/{len(NAMES)}] {name}: 调用失败 {str(e)[:100]}", flush=True)
    time.sleep(2)
print("完成", flush=True)
