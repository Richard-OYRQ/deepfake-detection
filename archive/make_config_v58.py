# -*- coding: utf-8 -*-
"""生成 v5.8 候选提示词 A/B 测试配置（仅替换 videos.prompt，其余保持 v5.7 基线）。"""
import sys

sys.path.insert(0, r"E:\DeepFake")
import yaml  # noqa: E402

NEW_PROMPT = open(r"E:\DeepFake\20260915\qwen3_vl_plus_prompt_v58_candidate.txt",
                  encoding="utf-8").read()

cfg = yaml.safe_load(open(r"E:\DeepFake\config.yaml", encoding="utf-8"))
cfg["videos"]["dir"] = "./_exp2"
cfg["videos"]["prompt"] = NEW_PROMPT
cfg["output"]["dir"] = "./output_v58"

with open(r"E:\DeepFake\config_v58.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print("config_v58.yaml 已生成（提示词长度:", len(NEW_PROMPT), "字符）")
