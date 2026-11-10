# -*- coding: utf-8 -*-
"""M2 基线训练：EfficientNet-B0 预训练微调（双分类：真实/伪造）。
- 类别加权采样平衡真伪比；AdamW + 余弦退火；30 轮早停（耐心 6 轮）
- 每轮记录训练/验证正确率与损失，保存最优权重 best_model.pth
- 输出 training/m2_output/：日志 CSV、训练曲线 PNG"""
import csv
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torchvision
from torch.utils.data import DataLoader, WeightedRandomSampler

from dataset import DeepfakeDataset
from augment import train_transforms, val_transforms

BASE = r"E:\deepfake"
OUT = os.path.join(BASE, "training", "m2_output")
os.makedirs(OUT, exist_ok=True)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EPOCHS = 30
BATCH = 32
LR = 1e-4
PATIENCE = 6

print(f"设备: {DEVICE}", flush=True)

train_ds = DeepfakeDataset("train", train_transforms())
val_ds = DeepfakeDataset("val", val_transforms())

# 双重加权采样：按（真伪 × 家族）分层，权重 = 1/层计数
# 保证小家族（如 inswapper 101 条）与大族（FaceShifter 1000 条）学习机会均等
from collections import Counter
stratum = [f"{r['标签']}_{r['家族']}" for r in train_ds.rows]
counts = Counter(stratum)
weights = [1.0 / counts[s] for s in stratum]
sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

train_dl = DataLoader(train_ds, batch_size=BATCH, sampler=sampler, num_workers=0)
val_dl = DataLoader(val_ds, batch_size=BATCH, shuffle=False, num_workers=0)
print(f"训练集 {len(train_ds)} 条 / 验证集 {len(val_ds)} 条", flush=True)

model = torchvision.models.efficientnet_b0(
    weights=torchvision.models.EfficientNet_B0_Weights.IMAGENET1K_V1)
model.classifier[1] = nn.Linear(1280, 2)
model = model.to(DEVICE)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

log_path = os.path.join(OUT, "train_log.csv")
ckpt_path = os.path.join(OUT, "checkpoint.pth")
start_epoch, best_acc, best_epoch, bad = 1, 0.0, 0, 0
if os.path.exists(ckpt_path):   # 断点续训
    ck = torch.load(ckpt_path, map_location=DEVICE)
    model.load_state_dict(ck["model"])
    optimizer.load_state_dict(ck["optimizer"])
    scheduler.load_state_dict(ck["scheduler"])
    start_epoch = ck["epoch"] + 1
    best_acc, best_epoch, bad = ck["best_acc"], ck["best_epoch"], ck["bad"]
    print(f"续训：从第 {start_epoch} 轮继续（当前最优 {best_acc:.3f}）", flush=True)
else:
    with open(log_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["epoch", "train_loss", "train_acc", "val_acc", "lr", "seconds"])

for epoch in range(start_epoch, EPOCHS + 1):
    t0 = time.time()
    model.train()
    total, correct, loss_sum = 0, 0, 0.0
    for imgs, y in train_dl:
        imgs, y = imgs.to(DEVICE), y.to(DEVICE)
        optimizer.zero_grad()
        out = model(imgs)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        loss_sum += loss.item() * len(y)
        total += len(y)
        correct += (out.argmax(1) == y).sum().item()
    train_loss = loss_sum / total
    train_acc = correct / total

    model.eval()
    v_total = v_correct = 0
    with torch.no_grad():
        for imgs, y in val_dl:
            imgs, y = imgs.to(DEVICE), y.to(DEVICE)
            out = model(imgs)
            v_total += len(y)
            v_correct += (out.argmax(1) == y).sum().item()
    val_acc = v_correct / v_total
    scheduler.step()

    with open(log_path, "a", newline="") as f:
        csv.writer(f).writerow([epoch, round(train_loss, 4), round(train_acc, 4),
                                round(val_acc, 4), round(scheduler.get_last_lr()[0], 7),
                                round(time.time() - t0, 1)])
    torch.save({"epoch": epoch, "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "best_acc": best_acc, "best_epoch": best_epoch, "bad": bad},
               ckpt_path)
    print(f"[{epoch}/{EPOCHS}] loss {train_loss:.4f} 训练正确率 {train_acc:.3f} "
          f"验证正确率 {val_acc:.3f} 用时 {time.time() - t0:.0f}s", flush=True)

    if val_acc > best_acc:
        best_acc, best_epoch, bad = val_acc, epoch, 0
        torch.save(model.state_dict(), os.path.join(OUT, "best_model.pth"))
    else:
        bad += 1
        if bad >= PATIENCE:
            print(f"早停：验证正确率连续 {PATIENCE} 轮未提升", flush=True)
            break

print(f"训练结束：最优验证正确率 {best_acc:.3f}（第 {best_epoch} 轮）-> {OUT}", flush=True)

# 训练曲线
rows = list(csv.DictReader(open(log_path)))
ep = [int(r["epoch"]) for r in rows]
tr = [float(r["train_acc"]) for r in rows]
va = [float(r["val_acc"]) for r in rows]
plt.figure(figsize=(8, 5))
plt.plot(ep, tr, label="训练正确率")
plt.plot(ep, va, label="验证正确率")
plt.axhline(0.675, color="red", linestyle="--", label="融合规则基线 67.5%")
plt.xlabel("轮次"); plt.ylabel("正确率"); plt.legend(); plt.grid(alpha=0.3)
plt.title("M2 基线训练曲线（EfficientNet-B0）")
plt.savefig(os.path.join(OUT, "train_curves.png"), dpi=150)
print("曲线已保存 train_curves.png", flush=True)
