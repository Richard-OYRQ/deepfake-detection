# -*- coding: utf-8 -*-
"""第0步：决策层离线重放消融。
复用 src/processor.py 的 _finalize_result，对 full200(200条)+exp6(6条) 带标签历史结果
重放多组阈值变体，统计伪造检出/真实误报/存疑率。

标签来源：用户约定（F开头=伪造，纯数字=真实）——仅用于结果分析，不参与检测。
老批次 full200 未存 vote_result，重放时 tally=None（投票相关规则仅 exp6 可测），
变体间相对比较仍然有效。
"""
import glob
import json
import sys

sys.path.insert(0, r"E:\deepfake")
from src.config import AppConfig
from src.processor import VideoProcessor

BASE_CFG = r"E:\deepfake\config_exp6.yaml"


def label_of(name: str) -> str:
    return "fake" if str(name).startswith("F") else "real"


# ---------- 装载数据 ----------
records = []

f = sorted(glob.glob(r"E:\deepfake\output_full200\results_*.json"))[-1]
d = json.load(open(f, encoding="utf-8"))
for r in d["results"]:
    rec = dict(r)
    rec["label"] = label_of(r["task_name"])
    rec["source"] = "full200"
    rec["vote_result"] = None  # 老批次未存票型，统一置 None
    records.append(rec)

f6 = sorted(glob.glob(r"E:\deepfake\output_exp6\results_*.json"))[-1]
d6 = json.load(open(f6, encoding="utf-8"))
for r in d6["results"]:
    rec = dict(r)
    rec["label"] = label_of(r["task_name"])
    rec["source"] = "exp6"
    records.append(rec)

n_fake = sum(1 for r in records if r["label"] == "fake")
n_real = sum(1 for r in records if r["label"] == "real")
print(f"装载 {len(records)} 条（伪造 {n_fake} / 真实 {n_real}）\n")

# ---------- 变体（只动终裁层消耗的阈值，不动调用流程） ----------
VARIANTS = {
    "V0 基线(v5.7现配置)": {},
    "V1 去定罪背靠(0.70→0)": {"prior_convict_backstop": 0.0},
    "V2 冲突阈值0.55→0.70": {"prior_conflict_threshold": 0.70},
    "V2b 冲突阈值0.55→0.45": {"prior_conflict_threshold": 0.45},
    "V3 物理守卫关闭(0.5→0)": {"phys_guard_threshold": 0.0},
    "V4 置信度85/90→80/85": {"final_fake_conf_threshold": 80, "final_real_conf_threshold": 85},
    "V5 简化=去背靠+无物理守卫": {"prior_convict_backstop": 0.0, "phys_guard_threshold": 0.0},
    "V6 激进=简化+冲突0.45+置信80/85": {"prior_convict_backstop": 0.0, "phys_guard_threshold": 0.0,
                              "prior_conflict_threshold": 0.45,
                              "final_fake_conf_threshold": 80, "final_real_conf_threshold": 85},
    "V7 纯模型票(定罪闸门0.70→0)": {"convict_prior": 0.0, "prior_convict_backstop": 0.0},
}


def make_proc(patches: dict) -> VideoProcessor:
    cfg = AppConfig.from_yaml(BASE_CFG)
    for k, v in patches.items():
        setattr(cfg, k, v)
    return VideoProcessor(cfg, None, None)


def replay_all(proc: VideoProcessor) -> list:
    out = []
    for r in records:
        rr = dict(r)
        proc._finalize_result(rr, prior_p=r.get("prior_p"),
                              phys_score=r.get("phys_score"),
                              highres=r.get("highres", False))
        out.append(rr)
    return out


def metrics(recs) -> dict:
    out = {}
    for lab in ("fake", "real"):
        sub = [r for r in recs if r["label"] == lab]
        out[lab] = {
            "n": len(sub),
            "伪造": sum(1 for r in sub if r.get("final_verdict") == "伪造"),
            "无伪造": sum(1 for r in sub if r.get("final_verdict") == "无伪造"),
            "存疑": sum(1 for r in sub if r.get("final_verdict") == "存疑"),
        }
    return out


# ---------- 自检：V0 重放 vs 历史记录 ----------
base_proc = make_proc({})
base_replay = replay_all(base_proc)
agree = 0
diverge = []
for r, rr in zip(records, base_replay):
    if rr.get("final_verdict") == r.get("final_verdict"):
        agree += 1
    else:
        diverge.append((r["source"], r["task_name"],
                        r.get("final_verdict"), rr.get("final_verdict"),
                        r.get("prior_p")))
print(f"自检: V0重放与历史终裁一致 {agree}/{len(records)}")
for x in diverge[:15]:
    print("  分歧:", x)
print()

# ---------- 各变体指标 ----------
print(f"{'变体':<38}{'伪造检出':>10}{'真实误报':>10}{'存疑(伪/真)':>14}")
for vname, patches in VARIANTS.items():
    rr = replay_all(make_proc(patches))
    m = metrics(rr)
    fk, fr = m["fake"], m["real"]
    print(f"{vname:<36}{fk['伪造']:>4}/{fk['n']:<5}{fr['伪造']:>4}/{fr['n']:<5}"
          f"{str(fk['存疑'])+'/'+str(fr['存疑']):>14}")

# ---------- exp6 单独看（纯伪造、字段完整） ----------
print("\nexp6 纯伪造 6 条（vote_result 完整）：")
for vname, patches in VARIANTS.items():
    rr = [r for r in replay_all(make_proc(patches)) if r["source"] == "exp6"]
    hit = sum(1 for r in rr if r.get("final_verdict") == "伪造")
    sus = sum(1 for r in rr if r.get("final_verdict") == "存疑")
    print(f"  {vname:<36} 伪造 {hit}/6  存疑 {sus}/6")

# ---------- 背靠阈值连续扫描（其余同 V5 简化） ----------
print("\n背靠阈值扫描（去物理守卫，其余同现配置）：")
for bs in (0.0, 0.45, 0.55, 0.60, 0.65, 0.70):
    rr = replay_all(make_proc({"prior_convict_backstop": bs, "phys_guard_threshold": 0.0}))
    m = metrics(rr)
    fk, fr = m["fake"], m["real"]
    print(f"  backstop={bs:<4}  伪造检出 {fk['伪造']:>3}/{fk['n']}  真实误报 {fr['伪造']}/{fr['n']}  "
          f"存疑 伪{fk['存疑']}/真{fr['存疑']}")

# ---------- V5 简化下被误报的 4 条真实视频细节 ----------
print("\nV5(去背靠)下真实视频被误判为伪造的明细：")
rr = replay_all(make_proc({"prior_convict_backstop": 0.0, "phys_guard_threshold": 0.0}))
for r in rr:
    if r["label"] == "real" and r.get("final_verdict") == "伪造":
        print(f"  {r['source']}/{r['task_name']}: prior={r.get('prior_p')} conf={r.get('final_confidence')} "
              f"highres={r.get('highres')}")

# ---------- V5 简化下被新捞回的伪造视频样例 ----------
print("\nV5(去背靠)下新增定罪的伪造视频（前12条）：")
base_ver = {r["source"] + "/" + r["task_name"]: r.get("final_verdict") for r in base_replay}
for r in rr:
    if r["label"] == "fake" and r.get("final_verdict") == "伪造" \
            and base_ver.get(r["source"] + "/" + r["task_name"]) != "伪造":
        print(f"  {r['source']}/{r['task_name']}: prior={r.get('prior_p')} conf={r.get('final_confidence')}")
