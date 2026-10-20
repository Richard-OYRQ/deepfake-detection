# -*- coding: utf-8 -*-
"""_self60 检测驱动：每批 5 条、断点续批（被杀后重跑自动跳过已完成批次）。"""
import glob
import json
import os
import shutil
import subprocess
import time

SRC = r"E:\deepfake\_self60"
labels = json.load(open(os.path.join(SRC, "labels.json"), encoding="utf-8"))
names = sorted(labels)
CHUNK = 5
PY = r"E:\deepfake\.venv314\Scripts\python.exe"
MAIN = r"E:\deepfake\main.py"
template = open(r"E:\deepfake\config_v511.yaml", encoding="utf-8").read()

n_batches = (len(names) + CHUNK - 1) // CHUNK
for i in range(0, len(names), CHUNK):
    chunk = names[i:i + CHUNK]
    n = i // CHUNK + 1
    outdir = rf"E:\deepfake\output_self60_c{n}"
    if glob.glob(os.path.join(outdir, "results_*.json")):
        print(f"[批次 {n}/{n_batches}] 已完成，跳过", flush=True)
        continue
    cdir = rf"E:\deepfake\_self60_c{n}"
    os.makedirs(cdir, exist_ok=True)
    sub = {}
    for k in chunk:
        dest = os.path.join(cdir, k)
        if not os.path.exists(dest):
            shutil.copy2(os.path.join(SRC, k), dest)
        sub[k] = labels[k]
    with open(os.path.join(cdir, "labels.json"), "w", encoding="utf-8") as fp:
        json.dump(sub, fp, ensure_ascii=False, indent=2)
    cfg = (template
           .replace('dir: "./_val100"', f'dir: "./_self60_c{n}"')
           .replace('dir: "./output_v511"', f'dir: "./output_self60_c{n}"')
           .replace('file: "./logs/run_v511.log"', f'file: "./logs/run_self60_c{n}.log"'))
    cfg_path = rf"E:\deepfake\config_self60_c{n}.yaml"
    with open(cfg_path, "w", encoding="utf-8") as fp:
        fp.write(cfg)
    print(f"[批次 {n}/{n_batches}] {len(chunk)} 条开始 ...", flush=True)
    pr = subprocess.run([PY, MAIN, "--config", cfg_path])
    print(f"[批次 {n}/{n_batches}] 退出码 {pr.returncode}", flush=True)
    if pr.returncode != 0:
        print("批次失败，终止。重跑本脚本可续跑。", flush=True)
        break
    time.sleep(10)
print("全部批次结束。", flush=True)
