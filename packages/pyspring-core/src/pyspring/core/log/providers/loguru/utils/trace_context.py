"""
from pyspring.core.log.instance import logger

日志追踪上下文接口
提供统一方式设置并使用带 trace_id 的日志
"""

from contextlib import contextmanager
from contextvars import ContextVar

from pyspring.core.log.instance import logger

# 仅保留一个上下文变量，供过滤器使用（LoguruConfig 会读取它以填充 extra[trace_id]）
_trace_id_ctx: ContextVar[(str) | None] = ContextVar("trace_id", default=None)


def trace_logger(trace_id: str):
    """设置追踪ID并返回绑定了 trace_id 的 logger（最简统一入口）。
    用法：
        log = trace_logger(trace_id)
        log.info("message")
    """
    _trace_id_ctx.set(trace_id)
    return logger.bind(trace_id=trace_id)


@contextmanager
def trace_logging(trace_id: str):
    """with 作用域方式使用追踪日志：进入时设置，退出时自动恢复。
    用法：
        with trace_logging(trace_id) as log:
            log.info("message")
    """
    token = _trace_id_ctx.set(trace_id)
    try:
        yield logger.bind(trace_id=trace_id)
    finally:
        _trace_id_ctx.reset(token)


def set_trace_id(trace_id: (str) | None) -> None:
    """设置当前追踪ID(可设置为None重置)"""
    _trace_id_ctx.set(trace_id)


def get_trace_id() -> (str) | None:
    """
    获取当前追踪ID
    """
    try:
        return _trace_id_ctx.get()
    except Exception:
        return None
