# -*- coding: utf-8 -*-
"""M1 第一步：数据盘点。扫描全部数据目录，生成带 路径/标签/家族/分辨率 的清单。
输出：data/数据清单.csv + 汇总统计。"""
import csv
import os
from collections import Counter

import cv2

BASE = r"E:\deepfake"
SOURCES = [
    (os.path.join(BASE, "videos"), "videos"),                # 纯数字=real，F=伪造
    (os.path.join(BASE, "待鉴别"), "待鉴别"),                 # 纯数字=real，F=伪造
    (os.path.join(BASE, "_self160"), "_self160"),            # 留出集：80真+80伪
    (os.path.join(BASE, r"外部评测集100\real"), "外部_real"),
    (os.path.join(BASE, r"外部评测集100\fake"), "外部_fake"),
]
FAMILY_PREFIX = ["Deepfakes", "FaceSwap", "DeepFakeDetection",
                 "Face2Face", "NeuralTextures", "FaceShifter"]
VIDEO_EXT = (".mp4", ".avi", ".mov", ".mkv")


def label_of(name, source):
    if source.startswith("外部"):
        return "real" if source.endswith("real") else "fake"
    return "real" if name[0].isdigit() else "fake"


def family_of(name, source, label):
    if label == "real":
        return "真实"
    if source.startswith("外部"):
        for p in FAMILY_PREFIX:
            if name.startswith(p + "_"):
                return p
        # 无方法前缀的 200 条：命名规律（场景_表情__视频码）与 DeeperForensics-1.0 一致，
        # 其伪造集由 DF-VAE（多对多换脸 VAE）生成（来源：DF-1.0 CVPR2020 论文）
        return "DF-VAE(DF1.0)"
    return "自建(inswapper)"


def bucket(w, h):
    if h >= 1080:
        return "1080p+"
    if h >= 720:
        return "720p"
    if h >= 480:
        return "480p"
    return f"<480p({h}p)"


rows = []
fail = 0
for dirpath, source in SOURCES:
    if not os.path.isdir(dirpath):
        print(f"目录不存在: {dirpath}")
        continue
    for name in sorted(os.listdir(dirpath)):
        if not name.lower().endswith(VIDEO_EXT):
            continue
        path = os.path.join(dirpath, name)
        label = label_of(name, source)
        family = family_of(name, source, label)
        cap = cv2.VideoCapture(path)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
        else:
            w = h = 0
            fail += 1
        size_mb = os.path.getsize(path) / 1048576
        rows.append({"来源": source, "文件名": name, "标签": label,
                     "家族": family, "宽": w, "高": h,
                     "分辨率档": bucket(w, h) if w else "不可读",
                     "大小MB": round(size_mb, 2)})

out_dir = os.path.join(BASE, "data")
os.makedirs(out_dir, exist_ok=True)
out_csv = os.path.join(out_dir, "数据清单.csv")
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    wcsv = csv.DictWriter(f, fieldnames=["来源", "文件名", "标签", "家族",
                                         "宽", "高", "分辨率档", "大小MB"])
    wcsv.writeheader()
    wcsv.writerows(rows)

print(f"清单已写入: {out_csv}（共 {len(rows)} 条，不可读 {fail}）")
print()
print("--- 按来源 x 标签 ---")
for (s, l), n in sorted(Counter((r["来源"], r["标签"]) for r in rows).items()):
    print(f"  {s:<12} {l:<5} {n}")
print("--- 按家族（伪造侧） ---")
for fam, n in sorted(Counter(r["家族"] for r in rows if r["标签"] == "fake").items(),
                     key=lambda x: -x[1]):
    print(f"  {fam:<20} {n}")
print("--- 分辨率分布 ---")
for b, n in sorted(Counter(r["分辨率档"] for r in rows).items(), key=lambda x: -x[1]):
    print(f"  {b:<12} {n}")
print("--- 跨目录同名文件（疑似拷贝重复） ---")
names = Counter(r["文件名"] for r in rows)
dup = {k: v for k, v in names.items() if v > 1}
print(f"  同名文件数: {len(dup)}（涉及 {sum(dup.values())} 条记录）")
