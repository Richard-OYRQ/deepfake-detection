"""
流控模块
-------
实现令牌桶（Token Bucket）算法，同时控制：
- 最大并发数（Semaphore）
- 每秒/每分钟请求数上限
- 请求间最小间隔
"""

import asyncio
import time
from threading import Lock


class RateLimiter:
    """
    令牌桶限流器。

    参数
    ----
    max_concurrent : int
        最大同时进行的请求数。
    requests_per_minute : float
        每分钟允许的请求数（同时控制请求速率）。
    min_interval : float
        两次请求之间的最小间隔（秒）。
    """

    def __init__(
        self,
        max_concurrent: int = 2,
        requests_per_minute: float = 5,
        min_interval: float = 2.0,
    ):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rate = requests_per_minute / 60.0  # 转为每秒速率
        self._min_interval = min_interval

        # 令牌桶状态
        self._tokens = float(requests_per_minute)
        self._max_tokens = float(requests_per_minute)
        self._last_refill = time.monotonic()
        self._lock = Lock()

        # 记录上一次请求时间（用于 min_interval）
        self._last_request_time = 0.0
        self._time_lock = Lock()

    def _refill(self):
        """补充令牌（需在锁内调用）。"""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._max_tokens, self._tokens + elapsed * self._rate)
        self._last_refill = now

    def _acquire_token(self) -> bool:
        """尝试获取一个令牌。"""
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    def _wait_time_for_token(self) -> float:
        """估算获取下一个令牌需要等待的秒数。"""
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                return 0.0
            return (1.0 - self._tokens) / self._rate

    async def acquire(self):
        """
        异步获取执行许可。

        先申请并发槽位（Semaphore），再等待令牌可用，
        最后确保满足最小请求间隔。
        """
        # 1. 获取并发槽
        await self._semaphore.acquire()

        # 2. 等待令牌
        while not self._acquire_token():
            wait = self._wait_time_for_token()
            await asyncio.sleep(wait + 0.05)

        # 3. 确保最小间隔
        with self._time_lock:
            now = time.monotonic()
            since_last = now - self._last_request_time
            if since_last < self._min_interval:
                await asyncio.sleep(self._min_interval - since_last)
            self._last_request_time = time.monotonic()

    def release(self):
        """释放并发槽位（请求完成后必须调用）。"""
        self._semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        self.release()
