"""
步骤日志模块
"""

import inspect
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

from app.shared.config.common import PROJECT_ROOT_STR

load_dotenv()

LOG_CONSOLE_ENABLE = os.getenv("LOG_CONSOLE_ENABLE", "True").upper() == "TRUE"
LOG_CONSOLE_LEVEL = os.getenv("LOG_CONSOLE_LEVEL", "INFO").upper()
LOG_FILE_ENABLE = os.getenv("LOG_FILE_ENABLE", "True").upper() == "TRUE"
LOG_FILE_LEVEL = os.getenv("LOG_FILE_LEVEL", "INFO").upper()
LOG_FILE_RETENTION = os.getenv("LOG_FILE_RETENTION", "7 days")
LOG_DIR = Path(PROJECT_ROOT_STR) / "logs"
LOG_FILE_PATH = LOG_DIR / "app_{time:YYYYMMDD}.log"
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name: <20}</cyan>:<cyan>{function: <15}</cyan>:<cyan>{line: <4}</cyan> - <level>{message}</level>"
)


def init_logger():
    logger.remove()

    if LOG_CONSOLE_ENABLE:
        logger.add(sys.stdout, level=LOG_CONSOLE_LEVEL, format=LOG_FORMAT, colorize=True, enqueue=True)

    if LOG_FILE_ENABLE:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        logger.add(
            LOG_FILE_PATH, level=LOG_FILE_LEVEL, format=LOG_FORMAT, retention=LOG_FILE_RETENTION,
            encoding="utf-8", enqueue=True, backtrace=True, diagnose=True
        )
    return logger


# def fix_log_position(record):
#     for frame in inspect.stack():
#         if "_logger.py" in frame.filename or "logger.py" in frame.filename or frame.function == "_log":
#             continue
#         record.update(name=Path(frame.filename).name, function=frame.function, line=frame.lineno)
#         break


# logger = init_logger().patch(fix_log_position)
logger = init_logger()

if __name__ == '__main__':
    logger.debug("调试")
    logger.info("信息")
    logger.warning("警告")
    logger.error("错误")
    try:
        result = 10 / 0
        logger.info(f"业务计算结果为：{result}")
    except Exception:
        # exception 必须用在 except 里面，会自动打印完整异常堆栈（定位 bug 用）
        logger.exception("业务异常，输出完整堆栈信息")

