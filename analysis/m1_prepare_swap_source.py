# -*- coding: utf-8 -*-
"""M1 调整1 准备：挑选 80 条真实视频作为 faceswapvideo.io 换脸素材。
规则：
- 自建真实（videos/ 纯数字命名）中排除留出集同名文件后全部入选（约 20 条），
  避免"同一素材既在训练伪造侧、又在留出真实侧"的内容泄漏；
- 不足部分从外部真实（FF++ real）随机补齐（seed=20261031），
  该 60 条在后续"外部冻结测试集"划分时排除，防止冲突；
- 全部复制到 _swap_source/，并生成操作清单。"""
import csv
import os
import random
import shutil

BASE = r"E:\deepfake"
random.seed(20261031)

rows = []
with open(os.path.join(BASE, "data", "数据清单.csv"), encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

holdout_names = {r["文件名"] for r in rows if r["来源"] == "_self160"}
self_real = [r for r in rows if r["来源"] == "videos" and r["标签"] == "real"
             and r["文件名"] not in holdout_names]
ext_real = [r for r in rows if r["来源"] == "外部_real"]

picks = list(self_real)
need = 80 - len(picks)
picks += random.sample(ext_real, need)

out_dir = os.path.join(BASE, "_swap_source")
os.makedirs(out_dir, exist_ok=True)
srcdir = {"videos": os.path.join(BASE, "videos"),
          "外部_real": os.path.join(BASE, "外部评测集100", "real")}

guide = ["# 换脸素材操作清单（80 条）\n",
         "素材位置：_swap_source/（已按 01~80 编号）\n",
         "操作步骤（faceswapvideo.io）：\n",
         "1. 打开网站，上传一条素材视频（_swap_source 里的编号文件）\n",
         "2. 上传一张目标人脸照片（建议用你自己的照片或公开素材，注意合规）\n",
         "3. 点击生成，等待处理完成后下载成品视频\n",
         "4. 把成品放到 E:\\deepfake\\_swap_output\\，命名随意，我来统一入库\n",
         "5. 重复 1–4，共 80 次（预计半天，可分两次做完）\n\n",
         "已选素材清单：\n"]
for i, r in enumerate(picks, 1):
    src = os.path.join(srcdir[r["来源"]], r["文件名"])
    dst = os.path.join(out_dir, f"{i:02d}_{r['来源']}_{r['文件名']}")
    shutil.copy2(src, dst)
    guide.append(f"{i:02d} | {r['来源']} | {r['文件名']} | {r['分辨率档']}\n")

with open(os.path.join(out_dir, "操作清单.md"), "w", encoding="utf-8") as f:
    f.writelines(guide)

print(f"已挑选 {len(picks)} 条（自建 {len(self_real)} + 外部 {len(picks) - len(self_real)}）")
print(f"复制到: {out_dir}，操作清单已生成")
