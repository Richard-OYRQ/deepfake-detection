# -*- coding: utf-8 -*-
"""探针：修复 av 依赖后，边界样本的唇同步特征与音轨情况。"""
import sys
import av

sys.path.insert(0, r"E:\deepfake\src")
from preprocessor import _lip_sync_scan  # noqa: E402

for v in ["F1", "F45", "F63", "F96", "14", "66", "86", "98", "F12", "F22"]:
    path = rf"E:\deepfake\videos\{v}.mp4"
    try:
        c = av.open(path)
        n_audio = len(c.streams.audio)
        dur = float(c.duration / av.time_base) if c.duration else -1
        c.close()
    except Exception as e:
        n_audio, dur = f"err:{e}", -1
    lip = _lip_sync_scan(path)
    print(f"{v:<4} 音轨={n_audio} 时长={dur if isinstance(dur,str) else round(dur,1)}s "
          f"lip={lip}")
