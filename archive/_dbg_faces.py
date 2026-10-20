# -*- coding: utf-8 -*-
"""诊断 6 条零信号视频：analyze_video 原始返回 + 各视频 LLM 内容里是否描述人脸。"""
import json
import glob
import sys

sys.path.insert(0, r"E:\deepfake\src")
from preprocessor import analyze_video  # noqa: E402

V = ["63", "88", "96", "F63", "F88", "F96", "14", "F64"]
print("===== analyze_video 返回 =====")
for v in V:
    r = analyze_video(rf"E:\deepfake\videos\{v}.mp4")
    keys = ("error", "verdict", "valid_frames", "total_frames")
    info = {k: r.get(k) for k in keys}
    summ = (r.get("summary") or "")[:80].replace("\n", " ")
    print(f"{v:<4} {info}  summary[:80]={summ!r}")

print("\n===== LLM 内容是否描述人脸（前 60 字）=====")
for v in ["63", "88", "96", "F63", "F88", "F96"]:
    content = ""
    for f in glob.glob(r"E:\deepfake\output_self160_c*\results_*.json"):
        d = json.load(open(f, encoding="utf-8"))
        for r in d["results"]:
            if r.get("task_name") == v:
                content = r.get("content") or ""
                break
        if content:
            break
    print(f"{v}: {content[:60]!r}")
