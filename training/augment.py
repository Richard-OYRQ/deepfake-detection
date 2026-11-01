# -*- coding: utf-8 -*-
"""M1 数据增强与预处理变换。
训练集：随机裁剪+翻转+色彩扰动+高斯模糊（美颜模拟）+低质量 JPEG 重编码（平台压缩模拟）。
验证/测试集：仅缩放+中心裁剪+归一化（不做增强，保证考试公平）。"""
import io
import random

import PIL.Image
import torchvision.transforms as T

MEAN = [0.485, 0.456, 0.406]   # ImageNet 预训练模型的标准归一化参数
STD = [0.229, 0.224, 0.225]


class JPEGCompress:
    """压缩模拟：按低质量 JPEG 重编码再解回，模拟短视频平台二次压缩。"""

    def __init__(self, q_min=25, q_max=60):
        self.q_min, self.q_max = q_min, q_max

    def __call__(self, img):
        q = random.randint(self.q_min, self.q_max)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q)
        buf.seek(0)
        return PIL.Image.open(buf).convert("RGB")


def train_transforms():
    return T.Compose([
        T.RandomResizedCrop(224, scale=(0.7, 1.0), ratio=(0.9, 1.1)),
        T.RandomHorizontalFlip(),
        T.ColorJitter(brightness=0.25, contrast=0.25, saturation=0.2, hue=0.02),
        T.GaussianBlur(kernel_size=3, sigma=(0.1, 1.5)),   # 美颜/柔焦模拟
        T.RandomApply([JPEGCompress()], p=0.5),            # 平台压缩模拟
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])


def val_transforms():
    return T.Compose([
        T.Resize(256),
        T.CenterCrop(224),
        T.ToTensor(),
        T.Normalize(MEAN, STD),
    ])
