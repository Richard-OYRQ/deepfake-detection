# -*- coding: utf-8 -*-
"""从源目录重建 _val100（V_* 来自 videos/，E_* 来自外部评测集100 的 real/fake 子目录）。"""
import json
import os
import shutil

VAL = r"E:\deepfake\_val100"
labels = json.load(open(os.path.join(VAL, "labels.json"), encoding="utf-8"))

def source_of(name):
    stem = name[:-4]  # 去掉 .mp4 扩展名
    if name.startswith("V_real_"):
        return os.path.join(r"E:\deepfake\videos", stem[len("V_real_"):] + ".mp4")
    if name.startswith("V_fake_"):
        return os.path.join(r"E:\deepfake\videos", stem[len("V_fake_"):] + ".mp4")
    if name.startswith("E_real_"):
        return os.path.join(r"E:\deepfake\外部评测集100\real", stem[len("E_real_"):] + ".mp4")
    if name.startswith("E_fake_"):
        return os.path.join(r"E:\deepfake\外部评测集100\fake", stem[len("E_fake_"):] + ".mp4")
    return None

ok = missing = 0
for name in labels:
    src = source_of(name)
    if src is None or not os.path.exists(src):
        missing += 1
        if missing <= 10:
            print("源缺失:", name, "->", src)
        continue
    shutil.copy2(src, os.path.join(VAL, name + ".mp4"))
    ok += 1
print(f"重建完成: {ok} 条，源缺失 {missing} 条")
