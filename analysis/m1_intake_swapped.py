# -*- coding: utf-8 -*-
"""M1 调整1 收尾：换脸成品质检入库。
- 质检：可打开、帧数>0、中部帧能检出人脸、文件>100KB
- 入库：按 01~80 顺序命名为 F101~F180，复制到 videos/
- 输出：data/换脸入库映射.csv（原素材 → 新名 → 质检结果）"""
import csv
import os
import shutil

import cv2

BASE = r"E:\deepfake"
SRC = os.path.join(BASE, "_swap_output")
DST = os.path.join(BASE, "videos")
face_det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

rows = []
ok = fail = 0
for idx in range(1, 81):
    src = os.path.join(SRC, f"{idx:02d}_swapped.mp4")
    new_name = f"F{100 + idx}.mp4"
    status = "OK"
    if not os.path.exists(src):
        status = "缺失"
    else:
        cap = cv2.VideoCapture(src)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, n // 2)
        ret, mid = cap.read()
        cap.release()
        if n <= 0 or w <= 0:
            status = "打不开"
        elif os.path.getsize(src) < 100 * 1024:
            status = "文件过小"
        elif not ret:
            status = "中部帧读取失败"
        else:
            gray = cv2.cvtColor(mid, cv2.COLOR_BGR2GRAY)
            faces = face_det.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
            if len(faces) == 0:
                status = "未检出人脸"
    if status == "OK":
        shutil.copy2(src, os.path.join(DST, new_name))
        ok += 1
    else:
        fail += 1
    rows.append({"编号": f"{idx:02d}", "新名": new_name, "质检": status})
    print(f"{idx:02d} -> {new_name}: {status}", flush=True)

out_csv = os.path.join(BASE, "data", "换脸入库映射.csv")
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["编号", "新名", "质检"])
    w.writeheader()
    w.writerows(rows)
print(f"\n入库完成：成功 {ok} / 失败 {fail} -> {out_csv}", flush=True)
