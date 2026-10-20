# -*- coding: utf-8 -*-
"""自建 200 条全量离线统计：把当前策略（v5.11 修正版）套用到 8/30 full200 历史结果上。
含：① 记录在案的 v5.6 成绩 vs 当前策略重放成绩；② 双口径（综合正确率/标准准确率）；
③ 分批次统计；④ 漏判/误报清单。限制：full200 未存票型（投票类规则不可重放）、
phys_score 未落盘、prior 为 8/30 快照。"""
import glob
import json
import sys

sys.path.insert(0, r"E:\deepfake")
from src.config import AppConfig
from src.processor import VideoProcessor

f = sorted(glob.glob(r"E:\deepfake\output_full200\results_*.json"))[-1]
records = json.load(open(f, encoding="utf-8"))["results"]


def label_of(name):
    return "fake" if str(name).startswith("F") else "real"


def batch_of(name):
    """按编号推断批次（学习计划：第1批30、第2批30、第3批30+补充10+）。"""
    import re
    m = re.match(r"F?(\d+)", str(name))
    n = int(m.group(1)) if m else 0
    return "批1" if n <= 30 else ("批2" if n <= 60 else "批3")


def replay(**patches):
    cfg = AppConfig.from_yaml(r"E:\deepfake\config_v511.yaml")
    for k, v in patches.items():
        setattr(cfg, k, v)
    proc = VideoProcessor(cfg, None, None)
    out = []
    for r in records:
        rr = dict(r)
        proc._finalize_result(rr, prior_p=r.get("prior_p"), phys_score=r.get("phys_score"),
                              highres=r.get("highres", False))
        rr["_label"] = label_of(r["task_name"])
        rr["_batch"] = batch_of(r["task_name"])
        out.append(rr)
    return out


def stats(recs):
    fk = [r for r in recs if r["_label"] == "fake"]
    rl = [r for r in recs if r["_label"] == "real"]
    def c(rs, v):
        return sum(1 for r in rs if r.get("final_verdict") == v)
    fake_hit, fake_miss, fake_sus = c(fk, "伪造"), c(fk, "无伪造"), c(fk, "存疑")
    real_fp, real_ok, real_sus = c(rl, "伪造"), c(rl, "无伪造"), c(rl, "存疑")
    total = len(recs)
    correct_hard = fake_hit + real_ok
    sus = fake_sus + real_sus
    wrong_hard = fake_miss + real_fp
    return {
        "检出": fake_hit, "漏判": fake_miss, "存疑伪": fake_sus,
        "误报": real_fp, "无伪造": real_ok, "存疑真": real_sus,
        "综合正确率": f"{(correct_hard + sus) / total * 100:.1f}%",
        "标准准确率": f"{correct_hard / total * 100:.1f}%",
        "存疑率": f"{sus / total * 100:.1f}%",
        "误判率": f"{real_fp / len(rl) * 100:.1f}%",
        "漏判率": f"{fake_miss / len(fk) * 100:.1f}%",
    }


def show(tag, recs):
    s = stats(recs)
    print(f"{tag}")
    print(f"  伪造100: 检出{s['检出']} 漏判{s['漏判']} 存疑{s['存疑伪']} | "
          f"真实100: 误报{s['误报']} 无伪造{s['无伪造']} 存疑{s['存疑真']}")
    print(f"  综合正确率{s['综合正确率']} | 标准准确率{s['标准准确率']} | "
          f"存疑率{s['存疑率']} | 误判率{s['误判率']} | 漏判率{s['漏判率']}")


# ① 记录在案的 v5.6 成绩单
recorded = []
for r in records:
    rr = dict(r)
    rr["_label"] = label_of(r["task_name"])
    rr["_batch"] = batch_of(r["task_name"])
    recorded.append(rr)
print("===== ① 8/30 记录在案（v5.6 时代策略）=====")
show("v5.6 记录", recorded)

# ② 当前策略重放
print("\n===== ② 当前策略（v5.11 修正版）重放 =====")
show("v5.11 修正版", replay())
show("v5.11 + 冲突0.45", replay(prior_conflict_threshold=0.45))
show("v5.11 + 冲突0.45 + 真95", replay(prior_conflict_threshold=0.45,
                                        final_real_conf_threshold=95))

# ③ 分批次（当前策略重放）
print("\n===== ③ 分批次（v5.11 修正版重放）=====")
cur = replay()
for b in ("批1", "批2", "批3"):
    sub = [r for r in cur if r["_batch"] == b]
    s = stats(sub)
    print(f"{b}({len(sub)}条): 检出{s['检出']} 漏判{s['漏判']} 误报{s['误报']} "
          f"无伪造{s['无伪造']} 存疑{s['存疑伪']+s['存疑真']} | 综合{s['综合正确率']} 标准{s['标准准确率']}")

# ④ 漏判/误报清单
print("\n===== ④ 当前策略下的漏判与误报清单 =====")
miss = [r for r in cur if r["_label"] == "fake" and r.get("final_verdict") == "无伪造"]
fp = [r for r in cur if r["_label"] == "real" and r.get("final_verdict") == "伪造"]
print(f"漏判 {len(miss)} 条:", [r['task_name'] for r in miss])
print(f"误报 {len(fp)} 条:", [r['task_name'] for r in fp])
