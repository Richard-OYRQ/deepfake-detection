# -*- coding: utf-8 -*-
"""M2 留出集考试：用 best_model.pth 在冻结留出集 160 条上逐视频判定
（每条抽 5 帧独立预测，多数票为最终判定），输出正确率、混淆矩阵与明细。"""
import csv
import os

import cv2
import torch
import torchvision
from torchvision import transforms as T

from augment import val_transforms
from facecrop import crop_face_neck

BASE = r"E:\deepfake"
MODEL = os.path.join(BASE, "training", "m2_output", "best_model.pth")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
K = 5
SRCDIR = {
    "_self160": os.path.join(BASE, "_self160"),
}

model = torchvision.models.efficientnet_b0()
model.classifier[1] = torch.nn.Linear(1280, 2)
model.load_state_dict(torch.load(MODEL, map_location=DEVICE))
model = model.to(DEVICE).eval()

with open(os.path.join(BASE, "data", "留出集清单.csv"), encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

results = []
hit = fp = miss = ok = 0
with torch.no_grad():
    for n, r in enumerate(rows, 1):
        src = os.path.join(SRCDIR[r["来源"]], r["文件名"])
        cap = cv2.VideoCapture(src)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        dur = total / fps if fps > 0 else 0
        votes = 0
        for i in range(K):
            t = dur * (0.2 + 0.6 * i / (K - 1)) * 1000
            cap.set(cv2.CAP_PROP_POS_MSEC, t)
            ret, frame = cap.read()
            if not ret:
                continue
            frame, _found = crop_face_neck(frame)   # 与训练同口径的人脸+面颈裁剪
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = T.ToPILImage()(frame)
            x = val_transforms()(img).unsqueeze(0).to(DEVICE)
            votes += int(model(x).argmax(1).item())  # 1=伪造
        cap.release()
        pred = "fake" if votes > K // 2 else "real"
        truth = r["标签"]
        if truth == "fake" and pred == "fake":
            hit += 1
        elif truth == "fake":
            miss += 1
        elif pred == "fake":
            fp += 1
        else:
            ok += 1
        results.append({"文件名": r["文件名"], "真实": truth, "预测": pred,
                        "伪造票": votes, "判定": "✓" if truth == pred else "✗"})
        if n % 20 == 0 or n == len(rows):
            print(f"[{n}/{len(rows)}]", flush=True)

acc = (hit + ok) / len(rows)
print(f"\n===== 留出集 160 条考试 =====")
print(f"抓对伪造 {hit}/80 | 错杀真实 {fp}/80 | 漏掉伪造 {miss} | 总正确率 {acc:.1%}")
print(f"融合规则基线 67.5%（抓对47/错杀19/漏33）")

with open(os.path.join(BASE, "training", "m2_output", "holdout_detail.csv"),
          "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["文件名", "真实", "预测", "伪造票", "判定"])
    w.writeheader()
    w.writerows(results)
print("明细已保存 holdout_detail.csv", flush=True)
