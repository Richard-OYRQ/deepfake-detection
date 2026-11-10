# -*- coding: utf-8 -*-
"""M1 PyTorch 数据读取器：从抽帧缓存读取，随机选帧 + 变换，输出（图像, 标签）。
用法：DeepfakeDataset(split='train', transforms=train_transforms())"""
import csv
import os
import random

import PIL.Image
from torch.utils.data import Dataset

BASE = r"E:\deepfake"
CACHE = os.path.join(BASE, "data", "frames_cache")
K = 5  # 与 m1_build_frame_cache.py 一致


class DeepfakeDataset(Dataset):
    def __init__(self, split, transforms,
                 split_csv=os.path.join(BASE, "data", "划分结果.csv")):
        with open(split_csv, encoding="utf-8-sig") as f:
            self.rows = [r for r in csv.DictReader(f) if r["划分"] == split]
        self.transforms = transforms
        if not self.rows:
            raise ValueError(f"划分 {split} 为空，先运行 m1_split.py 与 m1_build_frame_cache.py")

    def _frame(self, nid, i):
        p = os.path.join(CACHE, f"{nid}_{i}.jpg")   # 纯数字命名
        return PIL.Image.open(p).convert("RGB")

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        r = self.rows[idx]
        i = random.randrange(K)  # 每轮随机选帧，配合随机裁剪增加多样性
        img = self._frame(r["编号"], i)
        label = 1 if r["标签"] == "fake" else 0
        return self.transforms(img), label
