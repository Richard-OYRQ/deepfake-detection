# -*- coding: utf-8 -*-
"""v5.11 回归驱动（断点续批版）：跳过已有 results 的批次，被杀后重跑不浪费已完成部分。"""
import glob
import json
import os
import shutil
import subprocess
import time

SRC = r"E:\deepfake\_val100"
labels = json.load(open(os.path.join(SRC, "labels.json"), encoding="utf-8"))
names = sorted(labels)
CHUNK = 5
PY = r"E:\deepfake\.venv314\Scripts\python.exe"
MAIN = r"E:\deepfake\main.py"
template = open(r"E:\deepfake\config_v511.yaml", encoding="utf-8").read()

n_batches = (len(names) + CHUNK - 1) // CHUNK
done = skipped = 0
for i in range(0, len(names), CHUNK):
    chunk = names[i:i + CHUNK]
    n = i // CHUNK + 1
    outdir = rf"E:\deepfake\output_v511_c{n}"
    if glob.glob(os.path.join(outdir, "results_*.json")):
        skipped += 1
        print(f"[批次 {n}/{n_batches}] 已完成，跳过", flush=True)
        continue

    cdir = rf"E:\deepfake\_v511_c{n}"
    os.makedirs(cdir, exist_ok=True)
    sub = {}
    for k in chunk:
        dest = os.path.join(cdir, k + ".mp4")
        if not os.path.exists(dest):
            shutil.copy2(os.path.join(SRC, k + ".mp4"), dest)
        sub[k] = labels[k]
    with open(os.path.join(cdir, "labels.json"), "w", encoding="utf-8") as fp:
        json.dump(sub, fp, ensure_ascii=False, indent=2)

    cfg = (template
           .replace('dir: "./_val100"', f'dir: "./_v511_c{n}"')
           .replace('dir: "./output_v511"', f'dir: "./output_v511_c{n}"')
           .replace('file: "./logs/run_v511.log"', f'file: "./logs/run_v511_c{n}.log"'))
    cfg_path = rf"E:\deepfake\config_v511_c{n}.yaml"
    with open(cfg_path, "w", encoding="utf-8") as fp:
        fp.write(cfg)

    print(f"[批次 {n}/{n_batches}] {len(chunk)} 条开始 ...", flush=True)
    pr = subprocess.run([PY, MAIN, "--config", cfg_path])
    print(f"[批次 {n}/{n_batches}] 退出码 {pr.returncode}", flush=True)
    if pr.returncode != 0:
        print("批次失败，终止。重启本脚本可续跑。", flush=True)
        break
    done += 1
    time.sleep(15)

print(f"本次完成 {done} 批，跳过 {skipped} 批。全部结束。", flush=True)
