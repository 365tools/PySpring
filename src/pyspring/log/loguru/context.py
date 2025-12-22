"""
最简日志上下文接口
提供统一方式设置并使用带 session_id 的日志
"""
from contextlib import contextmanager
from contextvars import ContextVar
from pyspring.log.loguru.ins import logger
from typing import Optional

# 仅保留一个上下文变量，供过滤器使用（LoguruConfig 会读取它以填充 extra[session_id]）
_session_id_ctx: ContextVar[Optional[str]] = ContextVar("session_id", default=None)


def session_logger(session_id: str):
    """设置会话ID并返回绑定了 session_id 的 logger（最简统一入口）。
    用法：
        log = session_logger(session_id)
        log.info("message")
    """
    _session_id_ctx.set(session_id)
    return logger.bind(session_id=session_id)


@contextmanager
def session_logging(session_id: str):
    """with 作用域方式使用会话日志：进入时设置，退出时自动恢复。
    用法：
        with session_logging(session_id) as log:
            log.info("message")
    """
    token = _session_id_ctx.set(session_id)
    try:
        yield logger.bind(session_id=session_id)
    finally:
        _session_id_ctx.reset(token)


# 便捷辅助函数（兼容脚本检查用），不改变现有对外行为

def set_session_id(session_id: Optional[str]) -> None:
    """设置当前会话ID(可设置为None重置)"""
    _session_id_ctx.set(session_id)


def get_session_id() -> Optional[str]:
    """
    获取当前会话ID
    """
    try:
        return _session_id_ctx.get()
    except Exception as e:
        logger.error(f"🚨 {e}")
        return None
