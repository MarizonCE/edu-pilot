"""
负责提供大模型 api 速度限制的工具模块
"""
import asyncio
import time
from collections import deque
from typing import Deque
from app.shared.runtime.logger import logger

_GLOBAL_REQUESTS: Deque[float] = deque()
_RATE_LIMIT_LOCK = asyncio.Lock()


async def call_api_rate_limit(max_request_times: int = 27000, window_seconds: int = 60) -> None:
    """
    防止大模型 API 调用速率超过官方限制导致报错。
    :param max_request_times: 限制调用次数，未确保统计情况差异，这里只写到官网的 90%
    :param window_seconds: 窗口期 1 分钟
    """
    async with _RATE_LIMIT_LOCK:
        # 1. 清理滑动窗口外的过期请求时间戳，保证队列仅存窗口内的请求
        while _GLOBAL_REQUESTS:
            current_time = time.monotonic()
            if current_time - _GLOBAL_REQUESTS[0] < window_seconds:
                break
            _GLOBAL_REQUESTS.popleft()

        # 2. 窗口内请求数达到上限，计算并阻塞等待剩余时间
        if len(_GLOBAL_REQUESTS) >= max_request_times:
            sleep_duration = window_seconds - (time.monotonic() - _GLOBAL_REQUESTS[0])
            if sleep_duration > 0:
                logger.debug(f"触发 API 速率限制，窗口 {window_seconds} 秒内最多调用 {max_request_times} 次，"
                             f"需等待 {sleep_duration:.2f} 秒。")
                await asyncio.sleep(sleep_duration)
            current_time = time.monotonic()

            while _GLOBAL_REQUESTS and (current_time - _GLOBAL_REQUESTS[0] >= window_seconds):
                _GLOBAL_REQUESTS.popleft()

        # 3. 记录当前请求时间戳，加入滑动窗口队列
        _GLOBAL_REQUESTS.append(time.monotonic())
        logger.debug(f"API 请求时间戳已记录，当前 {window_seconds} 秒窗口内请求次数：{len(_GLOBAL_REQUESTS)}")


if __name__ == '__main__':
    async def test():
        for i in range(50000):
            await call_api_rate_limit()
            await asyncio.sleep(0.0001)
            print("模拟调用大模型")


    asyncio.run(test())
