# -*- coding: utf-8 -*-
"""证据图导出：对指定视频生成 CV 热力图/剖面图/事件帧并保存为图片文件。
用法：python export_evidence.py [视频名1.mp4 视频名2.mp4 ...]（不带参数用默认清单）。"""
import os
import sys

sys.path.insert(0, r"E:\deepfake")
import cv2
from src.preprocessor import extract_cv_evidence, extract_event_frames

OUT = r"E:\deepfake\evidence_gallery"
os.makedirs(OUT, exist_ok=True)

DEFAULT = [
    r"E:\deepfake\videos\86.mp4",          # 真实（边界样本）
    r"E:\deepfake\videos\F12.mp4",         # 伪造（定罪线）
    r"E:\deepfake\videos\F16.mp4",         # 伪造（融合漏判）
    r"E:\deepfake\videos\F43.mp4",         # 伪造（融合漏判）
    r"E:\deepfake\videos\15.mp4",          # 真实（phys 陷阱）
    r"E:\deepfake\外部评测集100\fake\NeuralTextures_070_057.mp4",  # 外部伪造
]

videos = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT

for v in videos:
    if not os.path.exists(v):
        print(f"缺失: {v}")
        continue
    stem = os.path.splitext(os.path.basename(v))[0]
    try:
        cv_imgs = extract_cv_evidence(v)
    except Exception as e:
        cv_imgs = []
        print(f"{stem}: CV证据图生成失败 {e}")
    try:
        ev_imgs = extract_event_frames(v)
    except Exception as e:
        ev_imgs = []
        print(f"{stem}: 事件帧生成失败 {e}")
    n = 0
    items = [("cv", x) for x in (cv_imgs or [])] + [("ev", x) for x in (ev_imgs or [])]
    for kind, d in items:
        img = d.get("image")
        if img is None:
            continue
        idx = 1
        if kind == "cv":
            # CV证据图顺序固定：1=纹理密度热力图 2=面颈清晰度剖面
            idx = 1 if "热力" in str(d.get("label", "")) or "1" in str(d.get("label", "")) else 2
            fname = f"{stem}__heatmap.jpg" if idx == 1 else f"{stem}__profile.jpg"
        else:
            ts = d.get("ts")
            fname = f"{stem}__event{n + 1}" + (f"_t{ts:.1f}s" if ts is not None else "") + ".jpg"
        ok = cv2.imwrite(os.path.join(OUT, fname), img)
        n += 1 if ok else 0
        print(f"  {'OK ' if ok else 'FAIL'} {fname}")
    print(f"{stem}: 共导出 {n} 张\n")
print(f"全部完成 → {OUT}")
