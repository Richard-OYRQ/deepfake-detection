# -*- coding: utf-8 -*-
"""把 _val100h 拆成 fake/real 两个子目录（各带 labels.json），供内存受限的分批运行。"""
import json
import os
import shutil

SRC = r"E:\deepfake\_val100h"
labels = json.load(open(os.path.join(SRC, "labels.json"), encoding="utf-8"))

for lab in ("fake", "real"):
    dst = os.path.join(SRC + "_" + lab)
    os.makedirs(dst, exist_ok=True)
    sub = {k: v for k, v in labels.items() if v == lab}
    for k in sub:
        shutil.copy2(os.path.join(SRC, k + ".mp4"), os.path.join(dst, k + ".mp4"))
    with open(os.path.join(dst, "labels.json"), "w", encoding="utf-8") as fp:
        json.dump(sub, fp, ensure_ascii=False, indent=2)
    print(f"{dst}: {len(sub)} 条")
