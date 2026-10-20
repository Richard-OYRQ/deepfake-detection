# -*- coding: utf-8 -*-
"""把 14 个检测视频的抽帧图片导出到 Conlect 文件夹，供人工甄别。
复用 src.preprocessor 的抽帧策略（与分析/检测时完全一致）。"""
import os
import sys

sys.path.insert(0, r"E:\DeepFake")
import cv2  # noqa: E402
from src.preprocessor import _extract_frames, extract_event_frames  # noqa: E402

ROOT = r"E:\DeepFake\Conlect"
GROUPS = [
    ("F_伪造1080P", r"E:\DeepFake\1080P"),
    ("T_真实1080T", r"E:\DeepFake\1080T"),
]


def save_img(path, img):
    ext = os.path.splitext(path)[1] or ".jpg"
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(path)


total_f, total_e = 0, 0
for gname, vdir in GROUPS:
    for vf in sorted(os.listdir(vdir)):
        vpath = os.path.join(vdir, vf)
        if not vf.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
            continue
        base = os.path.join(ROOT, gname, os.path.splitext(vf)[0])
        fdir = os.path.join(base, "frames")
        edir = os.path.join(base, "events")
        os.makedirs(fdir, exist_ok=True)
        os.makedirs(edir, exist_ok=True)

        frames = _extract_frames(vpath)
        for i, (ts, img) in enumerate(frames, 1):
            save_img(os.path.join(fdir, f"f{i:02d}_t{ts:05.1f}s.jpg"), img)

        events = extract_event_frames(vpath, max_images=4)
        for i, ev in enumerate(events, 1):
            label = str(ev.get("label", "event")).replace("/", "_").replace(" ", "")
            save_img(os.path.join(edir, f"e{i}_{label}_t{ev.get('ts', 0):05.1f}s.jpg"), ev["image"])

        total_f += len(frames)
        total_e += len(events)
        print(f"{gname}/{vf}: 分析帧 {len(frames)} 张, 事件图 {len(events)} 张", flush=True)

print(f"\n完成: 分析帧共 {total_f} 张, 事件图共 {total_e} 张 -> {ROOT}", flush=True)
