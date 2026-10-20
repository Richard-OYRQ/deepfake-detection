# -*- coding: utf-8 -*-
"""外部评测集 1000 视频分类：真伪/流派/分辨率/来源。"""
import collections
import json
import re

meta = json.load(open(r"E:\DeepFake\外部评测集100\bench_meta.json", encoding="utf-8"))
METHODS = ["DeepFakeDetection", "Deepfakes", "Face2Face", "FaceShifter", "FaceSwap", "NeuralTextures"]


def method_of(m):
    if m["kind"] == "real":
        return "真实"
    for mm in METHODS:
        if m["name"].startswith(mm + "_"):
            return mm
    return "未标注(FF++衍生)"


def source_of(m):
    if m["kind"] == "real":
        return "FF++c23" if re.match(r"^\d+\.mp4$", m["name"]) else "angads24"
    return "FF++c23" if method_of(m) != "未标注(FF++衍生)" else "angads24"


def res_of(m):
    return f"{m['w']}x{m['h']}" if "w" in m else "未知"


rows = [(m["name"], m["kind"], method_of(m), res_of(m), source_of(m)) for m in meta]

print("总条目:", len(rows))
errs = [m for m in meta if "probe_err" in m]
print("探测失败:", len(errs), [e["name"] for e in errs][:5])
print("\n== 真伪 x 流派 ==")
for k, v in sorted(collections.Counter((r[2],) for r in rows).items()):
    print(" ", k[0], v)
print("\n== 伪造流派 x 分辨率 ==")
for k, v in sorted(collections.Counter((r[2], r[3]) for r in rows if r[1] == "fake").items()):
    print(" ", k[0], k[1], v)
print("\n== 真实 x 分辨率 ==")
for k, v in sorted(collections.Counter((r[3],) for r in rows if r[1] == "real").items()):
    print(" ", k[0], v)

json.dump(rows, open(r"E:\DeepFake\外部评测集100\bench_rows.json", "w", encoding="utf-8"), ensure_ascii=False)
print("\nrows 已写出")
