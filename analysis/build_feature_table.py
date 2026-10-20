# -*- coding: utf-8 -*-
"""
构建 200 个已标注视频的预处理特征表
- videos/  (1-100):  真实视频  label=real
- 待鉴别/  (F1-F100): 伪造视频  label=fake
- 使用改进后的 v4.1 预处理 (src/preprocessor.analyze_video)
- 支持断点续跑：已完成的视频跳过
"""
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.preprocessor import analyze_video

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, 'output', 'feature_table.csv')
VIDEO_EXT = ('.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv')

FEATURE_FIELDS = [
    'video', 'label', 'duration',
    'valid_frames', 'face_sharp_mean', 'bg_sharp_mean', 'neck_sharp_mean',
    'ratio_mean', 'ratio_min', 'ratio_std', 'face_neck_ratio',
    'fluctuation', 'blur_frac', 'global_softening',
    'occl_edge_ratio', 'occl_edge_ratio_min', 'face_box_jitter', 'face_size_jitter',
    'noise_ratio', 'chroma_diff', 'rot_diff_energy', 'flow_consistency',
    'lip_sync_corr', 'lip_sync_lag',
    'verdict',
]


def get_duration(path):
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return 0.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cap.release()
    return total / fps


def process_one(video_path, label, name):
    t0 = time.time()
    result = analyze_video(video_path)
    dt = time.time() - t0
    if 'error' in result:
        print(f'[{name}] ERROR: {result["error"]}', flush=True)
        return None
    total = result.get('total_frames', 0)
    row = {
        'video': name,
        'label': label,
        'duration': round(get_duration(video_path), 2),
        'valid_frames': total,
        'face_sharp_mean': round(result.get('face_sharpness_mean', 0), 1),
        'bg_sharp_mean': round(result.get('bg_sharpness_mean', 0), 1),
        'neck_sharp_mean': round(result.get('neck_sharpness_mean') or 0, 1),
        'ratio_mean': result.get('ratio_mean', -1),
        'ratio_min': result.get('ratio_min', -1),
        'ratio_std': result.get('ratio_std', -1),
        'face_neck_ratio': result.get('face_neck_ratio') if result.get('face_neck_ratio') is not None else -1,
        'fluctuation': result.get('fluctuation', -1),
        'blur_frac': round(result.get('blur_frames', 0) / total, 3) if total else 0,
        'global_softening': 1 if result.get('is_global_softening') else 0,
        'occl_edge_ratio': result.get('occl_edge_ratio', 0),
        'occl_edge_ratio_min': result.get('occl_edge_ratio_min', 0),
        'face_box_jitter': result.get('face_box_jitter', 0),
        'face_size_jitter': result.get('face_size_jitter', 0),
        'noise_ratio': result.get('noise_ratio', 0),
        'chroma_diff': result.get('chroma_diff', 0),
        'rot_diff_energy': result.get('rot_diff_energy', 0),
        'flow_consistency': result.get('flow_consistency', 0),
        'lip_sync_corr': result.get('lip_sync_corr', 0),
        'lip_sync_lag': result.get('lip_sync_lag', 0),
        'verdict': result.get('verdict', ''),
    }
    print(f'[{name}] ok {dt:.1f}s valid={total} ratio={row["ratio_mean"]}', flush=True)
    return row


def discover():
    """
    标注规则（重要）：
    - videos/ 中纯数字命名（如 1.mp4, 100.mp4）= 真实视频
    - 待鉴别/ 中 F 命名（如 F1.mp4）= 伪造视频
    - videos/ 中也混有 F 命名文件（历史复制残留），跳过，避免重复/错标
    """
    tasks = []
    real_dir = os.path.join(BASE, 'videos')
    fake_dir = os.path.join(BASE, '待鉴别')
    for f in sorted(os.listdir(real_dir)):
        stem = os.path.splitext(f)[0]
        if f.lower().endswith(VIDEO_EXT) and stem.isdigit():
            tasks.append((os.path.join(real_dir, f), 'real', f))
    for f in sorted(os.listdir(fake_dir)):
        if f.lower().endswith(VIDEO_EXT):
            tasks.append((os.path.join(fake_dir, f), 'fake', f))
    return tasks


def main():
    tasks = discover()
    print(f'共 {len(tasks)} 个视频 (真实: {sum(1 for t in tasks if t[1]=="real")}, '
          f'伪造: {sum(1 for t in tasks if t[1]=="fake")})', flush=True)

    # 断点续跑：读取已完成
    done = set()
    existing_rows = []
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                done.add(row['video'])
                existing_rows.append(row)
        print(f'已有 {len(done)} 条记录，跳过续跑', flush=True)

    todo = [t for t in tasks if t[2] not in done]
    print(f'待处理 {len(todo)} 个', flush=True)

    # 增量写文件句柄
    out_f = open(CSV_PATH, 'a', encoding='utf-8-sig', newline='')
    writer = csv.DictWriter(out_f, fieldnames=FEATURE_FIELDS)
    if not existing_rows:
        writer.writeheader()
    out_f.flush()

    done_count = 0
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(process_one, p, lb, nm): (nm, lb) for p, lb, nm in todo}
        for fut in as_completed(futures):
            nm, lb = futures[fut]
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
            print(f'进度 {done_count}/{len(todo)}  已用 {elapsed/60:.1f}min  预计剩余 {eta/60:.1f}min', flush=True)
    out_f.close()
    print(f'完成。特征表: {CSV_PATH}', flush=True)


if __name__ == '__main__':
    main()
