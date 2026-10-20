# -*- coding: utf-8 -*-
"""
构建 200 视频稳定先验表（v2）：
- videos/ 纯数字命名 = 真实；F 命名 = 伪造（与检测实际扫描的目录一致）
- 每视频 stable_prior_probability(path, n_runs=3) 取中位数
- 增量保存，支持断点续跑
"""
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.preprocessor import stable_prior_probability

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, 'output', 'stable_prior_table.csv')
VIDEO_EXT = ('.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv')


def discover():
    tasks = []
    videos_dir = os.path.join(BASE, 'videos')
    for f in sorted(os.listdir(videos_dir)):
        if not f.lower().endswith(VIDEO_EXT):
            continue
        stem = os.path.splitext(f)[0]
        if stem.isdigit():
            tasks.append((os.path.join(videos_dir, f), 'real', f))
        elif stem.startswith('F'):
            tasks.append((os.path.join(videos_dir, f), 'fake', f))
    return tasks


def process_one(video_path, label, name):
    t0 = time.time()
    p = stable_prior_probability(video_path, n_runs=3)
    dt = time.time() - t0
    print(f'[{name}] prior={p if p is None else round(p,3)} {dt:.1f}s', flush=True)
    if p is None:
        return None
    return {'video': name, 'label': label, 'prior': round(p, 4)}


def main():
    tasks = discover()
    print(f'共 {len(tasks)} 个视频 (真实: {sum(1 for t in tasks if t[1]=="real")}, '
          f'伪造: {sum(1 for t in tasks if t[1]=="fake")})', flush=True)

    done = set()
    existing = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                done.add(row['video'])
                existing.append(row)
        print(f'已有 {len(done)} 条，跳过续跑', flush=True)

    todo = [t for t in tasks if t[2] not in done]
    print(f'待处理 {len(todo)} 个', flush=True)

    out_f = open(CSV_PATH, 'a', encoding='utf-8-sig', newline='')
    writer = csv.DictWriter(out_f, fieldnames=['video', 'label', 'prior'])
    if not existing:
        writer.writeheader()
    out_f.flush()

    done_count = 0
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(process_one, p, lb, nm): nm for p, lb, nm in todo}
        for fut in as_completed(futures):
            nm = futures[fut]
            try:
                row = fut.result()
            except Exception as e:
                print(f'[{nm}] EXCEPTION: {e}', flush=True)
                row = None
            if row is not None:
                writer.writerow(row)
                out_f.flush()
            done_count += 1
            elapsed = time.time() - t_start
            eta = elapsed / max(1, done_count) * (len(todo) - done_count)
            print(f'进度 {done_count}/{len(todo)}  已用 {elapsed/60:.1f}min  剩余约 {eta/60:.1f}min', flush=True)
    out_f.close()
    print(f'完成: {CSV_PATH}', flush=True)


if __name__ == '__main__':
    main()
