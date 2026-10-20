# -*- coding: utf-8 -*-
"""v5.11 全量回归驱动：_val100 的 100 条视频，每批 5 条、单独进程、批间休眠。
输出到 output_v511_c1..c20，分析脚本合并。"""
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
for i in range(0, len(names), CHUNK):
    chunk = names[i:i + CHUNK]
    n = i // CHUNK + 1
    cdir = rf"E:\deepfake\_v511_c{n}"
    os.makedirs(cdir, exist_ok=True)
    sub = {}
    for k in chunk:
        shutil.copy2(os.path.join(SRC, k + ".mp4"), os.path.join(cdir, k + ".mp4"))
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
        print("批次失败，终止后续。", flush=True)
        break
    time.sleep(15)

print("全部批次结束。", flush=True)
