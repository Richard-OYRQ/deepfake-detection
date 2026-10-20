# -*- coding: utf-8 -*-
"""分层抽样 100 个（50真实+50伪造）并硬链接到 _exp4。"""
import json
import os
import random
import shutil

random.seed(2026)
meta = json.load(open(r"E:\DeepFake\外部评测集100\bench_meta.json", encoding="utf-8"))
SRC = r"E:\DeepFake\外部评测集100"
DST = r"E:\DeepFake\_exp4"

METHODS = ["DeepFakeDetection", "Deepfakes", "Face2Face", "FaceShifter", "FaceSwap", "NeuralTextures"]


def tier(m):
    if "w" not in m:
        return "未知"
    return "高清" if (m["w"] >= 1280 and m["h"] >= 720) else "低清"


def link(m):
    src = os.path.join(SRC, m["kind"], m["name"])
    dst = os.path.join(DST, m["name"])
    if not os.path.exists(dst):
        os.link(src, dst)  # 硬链接


os.makedirs(DST, exist_ok=True)
picks = []

# 伪造：6 方法 × 7 + 未标注 8 = 50
for mm in METHODS:
    ms = [m for m in meta if m["kind"] == "fake" and m["name"].startswith(mm + "_")]
    picks += random.sample(ms, 7)
unl = [m for m in meta if m["kind"] == "fake" and m["name"] not in
       {m["name"] for m in picks} and not any(m["name"].startswith(x + "_") for x in METHODS)]
# 未标注 = 非方法前缀的 200 个 angads24
unl = [m for m in meta if m["kind"] == "fake" and
       not any(m["name"].startswith(x + "_") for x in METHODS)]
picks += random.sample(unl, 8)

# 真实：高清 25 + 低清 25 = 50
reals = [m for m in meta if m["kind"] == "real"]
hi = [m for m in reals if tier(m) == "高清"]
lo = [m for m in reals if tier(m) == "低清"]
picks += random.sample(hi, 25) + random.sample(lo, 25)

for m in picks:
    link(m)

print("抽样完成:", len(picks), "个 ->", DST)
from collections import Counter
c = Counter((m["kind"], tier(m)) for m in picks)
print("构成:", dict(c))
fakem = Counter((m["name"].split("_")[0],) for m in picks if m["kind"] == "fake")
print("伪造流派抽样:", dict(fakem))
