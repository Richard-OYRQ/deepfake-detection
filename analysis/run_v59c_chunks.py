# -*- coding: utf-8 -*-
"""v59c 超小批次驱动：每批 5 条视频、单独进程、批间休眠，避免内存不足被杀。
输出到 output_v59c_c1..c9，分析脚本自动合并。"""
import json
import os
import shutil
import subprocess
import time

SRC = r"E:\deepfake\_val100h"
labels = json.load(open(os.path.join(SRC, "labels.json"), encoding="utf-8"))
names = sorted(labels)
CHUNK = 5
PY = r"E:\deepfake\.venv314\Scripts\python.exe"
MAIN = r"E:\deepfake\main.py"

template = open(r"E:\deepfake\config_v59c_fake.yaml", encoding="utf-8").read()

n_batches = (len(names) + CHUNK - 1) // CHUNK
for i in range(0, len(names), CHUNK):
    chunk = names[i:i + CHUNK]
    n = i // CHUNK + 1
    cdir = rf"E:\deepfake\_v59c_c{n}"
    os.makedirs(cdir, exist_ok=True)
    sub = {}
    for k in chunk:
        shutil.copy2(os.path.join(SRC, k + ".mp4"), os.path.join(cdir, k + ".mp4"))
        sub[k] = labels[k]
    with open(os.path.join(cdir, "labels.json"), "w", encoding="utf-8") as fp:
        json.dump(sub, fp, ensure_ascii=False, indent=2)

    cfg = (template
           .replace('dir: "./_val100h_fake"', f'dir: "./_v59c_c{n}"')
           .replace('dir: "./output_v59c_fake"', f'dir: "./output_v59c_c{n}"')
           .replace('file: "./logs/run_v59c_fake.log"', f'file: "./logs/run_v59c_c{n}.log"'))
    cfg_path = rf"E:\deepfake\config_v59c_c{n}.yaml"
    with open(cfg_path, "w", encoding="utf-8") as fp:
        fp.write(cfg)

    print(f"[批次 {n}/{n_batches}] {len(chunk)} 条视频开始 ...", flush=True)
    pr = subprocess.run([PY, MAIN, "--config", cfg_path])
    print(f"[批次 {n}/{n_batches}] 退出码 {pr.returncode}", flush=True)
    if pr.returncode != 0:
        print("批次失败，终止后续。", flush=True)
        break
    time.sleep(15)  # 批间休眠，让系统回收内存

print("全部批次结束。", flush=True)
