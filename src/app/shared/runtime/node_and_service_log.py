"""
节点和业务日志模块
"""
import functools
import inspect
import time
from typing import Mapping

from app.shared.runtime.logger import logger


def _trace_id(state) -> str:
    """获取任务 ID 或会话 ID"""
    if isinstance(state, Mapping):
        return str(state.get("session_id") or state.get("task_id") or "-")
    return "-"


def node_log(node_name: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(state, *args, **kwargs):
            trace_id = _trace_id(state)
            start_ts = time.time()
            logger.info(f"【{node_name}】节点开始，追踪 ID = {trace_id}")
            try:
                result = func(state, *args, **kwargs)
                cost_ms = int((time.time() - start_ts) * 1000)
                logger.info(f"【{node_name}】节点完成，追踪 ID = {trace_id}，耗时 = {cost_ms} ms")
                return result
            except Exception:
                logger.exception(f"【{node_name}】节点异常，追踪 ID = {trace_id}")
                raise

        return wrapper

    return decorator


def service_log(step_name: str):
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_ts = time.time()
                logger.info(f"【{step_name}】步骤开始")
                try:
                    result = await func(*args, **kwargs)
                    cost_ms = int((time.time() - start_ts) * 1000)
                    logger.info(f"【{step_name}】步骤完成，耗时 = {cost_ms} ms")
                    return result
                except Exception:
                    logger.exception(f"【{step_name}】步骤异常")
                    raise

            return async_wrapper
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_ts = time.time()
            logger.info(f"【{step_name}】步骤开始")
            try:
                result = func(*args, **kwargs)
                cost_ms = int((time.time() - start_ts) * 1000)
                logger.info(f"【{step_name}】步骤完成，耗时 = {cost_ms} ms")
                return result
            except Exception:
                logger.exception(f"【{step_name}】步骤异常")
                raise

        return wrapper

    return decorator
