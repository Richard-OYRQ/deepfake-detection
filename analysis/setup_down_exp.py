# -*- coding: utf-8 -*-
"""降分辨率对照实验准备：
取外部高清伪造 21 条 + 外部高清真实 22 条，ffmpeg 降清到 854 宽（保留音频），
复制到 _down_exp，写 labels.json。基线 = output_v58final 中同一批视频的原始高清结果。
"""
import glob
import json
import os
import subprocess

VAL = r"E:\deepfake\_val100"
OUT = r"E:\deepfake\_down_exp"

labels = {os.path.splitext(k)[0]: v for k, v in
          json.load(open(os.path.join(VAL, "labels.json"), encoding="utf-8")).items()}
d = json.load(open(sorted(glob.glob(r"E:\deepfake\output_v58final\results_*.json"))[-1],
                 encoding="utf-8"))

picks = []
for r in d["results"]:
    name = r["task_name"]
    if name.startswith("E_") and r.get("highres"):
        picks.append(name)
fake_n = sum(1 for n in picks if labels.get(n) == "fake")
real_n = sum(1 for n in picks if labels.get(n) == "real")
print(f"选中 {len(picks)} 条（伪造 {fake_n} / 真实 {real_n}）")

os.makedirs(OUT, exist_ok=True)
labels_out = {}
ok = fail = 0
for name in picks:
    src = os.path.join(VAL, name + ".mp4")
    dest = os.path.join(OUT, name + ".mp4")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-i", src,
           "-vf", "scale=854:-2:flags=bicubic",
           "-c:v", "libx264", "-preset", "fast", "-crf", "23",
           "-c:a", "aac", "-b:a", "96k",
           dest]
    pr = subprocess.run(cmd, capture_output=True, text=True)
    if pr.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 0:
        ok += 1
        labels_out[name] = labels[name]
    else:
        fail += 1
        print(f"FAIL {name}: {pr.stderr[:200]}")

with open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8") as fp:
    json.dump(labels_out, fp, ensure_ascii=False, indent=2)
print(f"完成: 降清成功 {ok}, 失败 {fail}")
