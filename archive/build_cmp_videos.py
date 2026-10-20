# -*- coding: utf-8 -*-
"""构建14个拼接对比视频：真+假拼为一段（各15秒）。
位置平衡：奇数对真实在前、偶数对假脸在前（排除位置偏差）。"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r'D:\deepfake'
FFMPEG = r'D:\facefusion\bin\ffmpeg.exe'
OUT_DIR = os.path.join(BASE, '_paircmp')
os.makedirs(OUT_DIR, exist_ok=True)

NUMS = [3, 5, 6, 7, 8, 10, 11, 12, 14, 15, 18, 19, 20, 22]
order = {}
for i, n in enumerate(NUMS):
    real_first = (i % 2 == 0)  # 奇数索引真实在前
    real = os.path.join(BASE, 'videos', '%d.mp4' % n)
    fake = os.path.join(BASE, 'pairset', 'outputs', 'fake_e%d_on_%d.mp4' % (n, n))
    out = os.path.join(OUT_DIR, 'cmp_%d.mp4' % n)
    first, second = (real, fake) if real_first else (fake, real)
    cmd = [FFMPEG, '-y', '-i', first, '-i', second,
           '-filter_complex',
           '[0:v]trim=duration=15,setpts=PTS-STARTPTS[a];'
           '[1:v]trim=duration=15,setpts=PTS-STARTPTS[b];'
           '[a][b]concat=n=2:v=1:a=0[v]',
           '-map', '[v]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(n, '失败:', r.stderr[-200:])
        continue
    order['cmp_%d' % n] = {'first': 'real' if real_first else 'fake',
                           'real_first': real_first, 'n': n}
    print('cmp_%d.mp4 就绪（%s在前）' % (n, '真实' if real_first else '假脸'))

with open(os.path.join(OUT_DIR, 'order.json'), 'w', encoding='utf-8') as f:
    json.dump(order, f, ensure_ascii=False, indent=2)
print('order.json 已记录拼接顺序')
