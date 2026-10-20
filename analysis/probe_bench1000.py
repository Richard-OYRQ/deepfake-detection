# -*- coding: utf-8 -*-
"""探测外部评测集 1000 个视频的分辨率，输出 JSON 元数据。"""
import json
import os
import subprocess

FFPROBE = r"E:\DeepFake\tools\ffmpeg-9.0.1-essentials_build\bin\ffprobe.exe"
ROOT = r"E:\DeepFake\外部评测集100"
OUT = os.path.join(ROOT, "bench_meta.json")

meta = []
for kind in ("real", "fake"):
    d = os.path.join(ROOT, kind)
    files = sorted(os.listdir(d))
    for i, name in enumerate(files, 1):
        path = os.path.join(d, name)
        if not name.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
            continue
        rec = {"name": name, "kind": kind}
        try:
            r = subprocess.run(
                [FFPROBE, "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", path],
                capture_output=True, text=True, timeout=60)
            out = r.stdout.strip()
            if out and "x" in out:
                w, h = out.split("x")
                rec["w"], rec["h"] = int(w), int(h)
            else:
                rec["probe_err"] = (r.stderr or "no output")[:80]
        except Exception as e:
            rec["probe_err"] = str(e)[:80]
        meta.append(rec)
        if i % 100 == 0:
            print(f"{kind} 进度 {i}/{len(files)}", flush=True)

json.dump(meta, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("探测完成:", len(meta), "条 ->", OUT, flush=True)
