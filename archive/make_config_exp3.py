# -*- coding: utf-8 -*-
"""生成实验3配置：backstop 0.50 + 新提示词（17项）+ 输出到 output_exp3。"""
import sys

sys.path.insert(0, r"E:\DeepFake")
import yaml  # noqa: E402
from prompt_v2_exp3 import PROMPT_V2  # noqa: E402

cfg = yaml.safe_load(open(r"E:\DeepFake\config.yaml", encoding="utf-8"))
cfg["strategy"]["prior_convict_backstop"] = 0.50
cfg["videos"]["dir"] = "./_exp2"
cfg["videos"]["prompt"] = PROMPT_V2
cfg["output"]["dir"] = "./output_exp3"

with open(r"E:\DeepFake\config_exp3.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
print("config_exp3.yaml 已生成")
