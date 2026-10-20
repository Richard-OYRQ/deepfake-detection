# -*- coding: utf-8 -*-
"""v5.10 方案1：辩护人清账轮。
对 v59c 的 38 条"存疑"样本，补一轮辩护人 3 票复核：
提示词 = 16项主提示词 + 【上一轮控方复核结论（供逐条质证）】 + 辩护人后缀。
终裁复用 _finalize_result（v59c 同款规则，prosecutor_round=False，highres=True，
先验复用 v59c 存储值）。只做 API 调用与文本处理，不提取证据图 → 内存轻量。
"""
import glob
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"E:\deepfake")
from src.config import AppConfig
from src.client import QwenClient
from src.processor import VideoProcessor, _parse_verdict, _parse_confidence

CFG_PATH = r"E:\deepfake\config_v59c_fake.yaml"
VIDEO_DIR = r"E:\deepfake\_val100h"
OUT = r"E:\deepfake\output_v510"

# ---- 装载 v59c 结果（9 个分块合并），挑出"存疑"样本 ----
v59c = {}
for f in sorted(glob.glob(r"E:\deepfake\output_v59c_c*\results_*.json")):
    for r in json.load(open(f, encoding="utf-8"))["results"]:
        v59c[r["task_name"]] = r
flagged = {n: r for n, r in v59c.items() if r.get("final_verdict") == "存疑"}
print(f"v59c 共 {len(v59c)} 条，存疑样本 {len(flagged)} 条", flush=True)

cfg = AppConfig.from_yaml(CFG_PATH)
client = QwenClient(cfg)
proc = VideoProcessor(cfg, None, None)
labels = json.load(open(os.path.join(r"E:\deepfake\_val100h", "labels.json"), encoding="utf-8"))


def defender_prompt(prior_content: str) -> str:
    return (cfg.default_prompt
            + "\n\n【上一轮控方复核结论（请逐条质证其引用证据，重点找美颜/压缩/光照的良性解释）】\n"
            + prior_content[:8000]
            + "\n\n" + cfg.defender_suffix)


def one_video(name, prior_r):
    """辩护人 3 票，多数票 + _finalize_result 终裁。"""
    path = os.path.join(VIDEO_DIR, name + ".mp4")
    prompt = defender_prompt(prior_r.get("content", ""))
    votes = []
    for v in range(3):
        task = {"name": name, "video_path": path, "prompt": prompt, "extra_images": []}
        res = client.call(task)
        time.sleep(cfg.min_interval_seconds)
        if res.get("error") is None and res.get("content"):
            votes.append(res)
    if not votes:
        return {**prior_r, "defender_round": "failed"}
    tally = {}
    for vv in votes:
        vd = _parse_verdict(vv.get("content", ""))
        tally[vd] = tally.get(vd, 0) + 1
    mc = max(tally.items(), key=lambda x: x[1])
    winner = next(vv for vv in votes if _parse_verdict(vv.get("content", "")) == mc[0])
    rr = dict(winner)
    rr["vote_result"] = tally
    rr["prosecutor_round"] = False
    rr["defender_round"] = True
    proc._finalize_result(rr, prior_p=prior_r.get("prior_p"), phys_score=None, highres=True)
    rr["prior_p"] = prior_r.get("prior_p")
    return rr


print(f"开始辩护人清账轮：{len(flagged)} 条 × 3 票，并发 2 ...", flush=True)
results = {}
names = sorted(flagged)
with ThreadPoolExecutor(max_workers=2) as ex:
    for name, rr in zip(names, ex.map(lambda n: one_video(n, flagged[n]), names)):
        results[name] = rr
        print(f"[{len(results)}/{len(names)}] {name}  v59c存疑 → v5.10 {rr.get('final_verdict')}"
              f"  (labels={labels.get(name)})", flush=True)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "defender_results.json"), "w", encoding="utf-8") as fp:
    json.dump({n: {k: r.get(k) for k in ("final_verdict", "final_confidence", "prior_p",
                                         "vote_result", "defender_round")}
               for n, r in results.items()}, fp, ensure_ascii=False, indent=2)

# ---- 汇总（v59c vs v5.10，含未被挑战的样本） ----
def tally(d, lab):
    t = {"伪造": 0, "无伪造": 0, "存疑": 0}
    for n, r in d.items():
        if labels.get(n) == lab:
            t[r.get("final_verdict", "存疑")] = t.get(r.get("final_verdict", "存疑"), 0) + 1
    return t

v510_all = dict(v59c)
v510_all.update(results)
print("\n=== v59c vs v5.10(方案1) ===", flush=True)
for name, d in (("v59c", v59c), ("v5.10", v510_all)):
    fk, rl = tally(d, "fake"), tally(d, "real")
    print(f"{name}: 伪造 检出{fk['伪造']}/漏判{fk['无伪造']}/存疑{fk['存疑']}  |  "
          f"真实 误报{rl['伪造']}/无伪造{rl['无伪造']}/存疑{rl['存疑']}", flush=True)
print("完成", flush=True)
