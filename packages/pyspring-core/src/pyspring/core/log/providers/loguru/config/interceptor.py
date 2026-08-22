"""
标准库日志拦截器 - 将标准库 logging 日志重定向到 Loguru

支持拦截 uvicorn、fastapi、watchfiles 等常见库的日志。
"""

import logging
import sys
from typing import Any

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    拦截标准库 logging 并重定向到 Loguru
    """

    def emit(self, record):
        """
        处理日志记录

        Args:
            record: logging.LogRecord 对象
        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 使用可选的帧处理以获取正确的调用者信息
        frame = sys._getframe(6)
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            if frame.f_back:
                frame = frame.f_back
                depth += 1
            else:
                break

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class WatchfilesFilter(logging.Filter):
    """
    过滤 watchfiles 的 "changes detected" 消息
    """

    def __init__(self, suppress_changes: bool = True):
        """
        初始化过滤器

        Args:
            suppress_changes: 是否抑制 "changes detected" 消息
        """
        super().__init__()
        self.suppress_changes = suppress_changes

    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录

        Args:
            record: logging.LogRecord 对象

        Returns:
            bool: True 表示保留，False 表示过滤
        """
        if self.suppress_changes:
            msg = str(record.getMessage()).lower()
            if "changes detected" in msg:
                return False
        return True


def setup_stdlib_intercept(intercept_config: dict[str, Any]) -> None:
    """
    根据配置设置标准库 logging 的拦截器

    Args:
        intercept_config: 拦截配置字典
    """
    # 配置标准库logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 获取根logger并强制使用我们的处理器
    root_logger = logging.getLogger()
    root_logger.handlers = [InterceptHandler()]
    root_logger.propagate = False
    root_logger.setLevel(0)

    # 根据配置决定要拦截的logger
    loggers_to_intercept = []

    if intercept_config.get("uvicorn", True):
        loggers_to_intercept.extend(["uvicorn", "uvicorn.error", "uvicorn.access"])

    if intercept_config.get("fastapi", True):
        loggers_to_intercept.append("fastapi")

    if intercept_config.get("watchfiles", True):
        # 除了拦截，还对 watchfiles 的 "changes detected" 类消息做抑制
        suppress_changes = True  # 默认启用抑制

        loggers_to_intercept.extend(["watchfiles", "watchfiles.main"])
        for name in ["watchfiles", "watchfiles.main"]:
            lgr = logging.getLogger(name)
            lgr.addFilter(WatchfilesFilter(suppress_changes))

    # 拦截自定义日志记录器
    custom_loggers = intercept_config.get("custom_loggers", [])
    loggers_to_intercept.extend(custom_loggers)

    # 应用拦截器
    for logger_name in loggers_to_intercept:
        stdlib_logger = logging.getLogger(logger_name)
        stdlib_logger.handlers = [InterceptHandler()]
        stdlib_logger.propagate = False
        stdlib_logger.setLevel(0)


__all__ = [
    "InterceptHandler",
    "WatchfilesFilter",
    "setup_stdlib_intercept",
]
