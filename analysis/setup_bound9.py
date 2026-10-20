# -*- coding: utf-8 -*-
"""④ 温度分层实验准备：复制 9 条边界样本到 _bound9，写 labels.json。"""
import json
import os
import shutil

PLAN = [
    ("F12.mp4", "fake", r"E:\deepfake\videos"),
    ("F15.mp4", "fake", r"E:\deepfake\videos"),
    ("F22.mp4", "fake", r"E:\deepfake\videos"),
    ("F23.mp4", "fake", r"E:\deepfake\videos"),
    ("F26.mp4", "fake", r"E:\deepfake\videos"),
    ("F73.mp4", "fake", r"E:\deepfake\videos"),
    ("F87.mp4", "fake", r"E:\deepfake\videos"),
    ("86.mp4", "real", r"E:\deepfake\videos"),
    ("NeuralTextures_070_057.mp4", "fake", r"E:\deepfake\外部评测集100\fake"),
]

OUT = r"E:\deepfake\_bound9"
os.makedirs(OUT, exist_ok=True)
labels = {}
for fname, lab, src_dir in PLAN:
    shutil.copy2(os.path.join(src_dir, fname), os.path.join(OUT, fname))
    labels[fname] = lab
with open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8") as fp:
    json.dump(labels, fp, ensure_ascii=False, indent=2)
print(f"完成：{len(labels)} 条 → _bound9")
