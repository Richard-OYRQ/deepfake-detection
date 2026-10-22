# -*- coding: utf-8 -*-
"""从 FF++ c23 压缩包再抽 1000 条：重演类 500（Face2Face 250 + NeuralTextures 250）
+ 第二代 500（FaceShifter 500），排除已下载文件。
沿用 remotezip 流式抽文件 + 429 指数退避 + 0.3s 限速。seed=20261022。"""
import os
import random
import shutil
import time
from remotezip import RemoteZip

URL = "https://hf-mirror.com/datasets/bitmind/FaceForensicsC23/resolve/main/FaceForensics%2B%2B_C23.zip"
OUT = r"E:\DeepFake\外部评测集100"
random.seed(20261022)

existing_fake = set(os.listdir(os.path.join(OUT, "fake")))


def make_session():
    """带 30s 超时的 requests 会话：防止连接停滞导致脚本永久挂起。"""
    import requests
    from requests.adapters import HTTPAdapter

    class TimeoutAdapter(HTTPAdapter):
        def send(self, *args, **kwargs):
            kwargs.setdefault("timeout", 30)
            return super().send(*args, **kwargs)

    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    s.mount("https://", TimeoutAdapter())
    return s


def open_zip(retries=6):
    for attempt in range(1, retries + 1):
        try:
            return RemoteZip(URL, session=make_session())
        except Exception:
            wait = 60 * 2 ** (attempt - 1)
            print(f"初始化被限流，{wait}s 后重试（{attempt}/{retries}）", flush=True)
            time.sleep(wait)
    raise RuntimeError("多次重试仍被限流，请稍后再运行")


z = open_zip()
infos = [i for i in z.infolist() if i.filename.endswith(".mp4")]

methods = {"Face2Face": 250, "NeuralTextures": 250, "FaceShifter": 500}

picks = []
for m, n_target in methods.items():
    pool = [i for i in infos if f"/fake/{m}/" in i.filename
            and f"{m}_{i.filename.split('/')[-1]}" not in existing_fake]
    n = min(n_target, len(pool))
    print(f"{m} 候选 {len(pool)} 条，抽取 {n} 条", flush=True)
    for i in random.sample(pool, n):
        picks.append((i, f"{m}_{i.filename.split('/')[-1]}"))

print(f"共 {len(picks)} 条待下载", flush=True)


def fetch_to(info, dest):
    for attempt in range(3):
        try:
            with z.open(info) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst, length=1 << 20)
            return True
        except Exception:
            if attempt == 2:
                return False
            time.sleep(3)


ok = fail = 0
dest_dir = os.path.join(OUT, "fake")
for n, (info, fname) in enumerate(picks, 1):
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        ok += 1
    elif fetch_to(info, dest):
        ok += 1
    else:
        fail += 1
        print(f"  FAIL {fname}", flush=True)
    time.sleep(0.3)
    if n % 50 == 0 or n == len(picks):
        print(f"[{n}/{len(picks)}] 完成 {ok} / 失败 {fail}", flush=True)

print(f"全部结束：成功 {ok}，失败 {fail}", flush=True)
