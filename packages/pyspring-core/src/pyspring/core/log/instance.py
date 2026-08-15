"""
全局日志实例

提供全局 logger 单例供应用使用。

设计说明（解耦 / 弱依赖）：
- 此处 logger 采用【惰性代理】：模块加载时不会立即构造底层日志服务
  （那会触发 loguru 提供者的全量初始化，进而反向依赖本模块形成循环导入）。
- 真正第一次调用日志方法时，才通过 LogManager 实例化具体实现。
- 因此 `from pyspring.core.log.instance import logger` 在任意模块顶层都是安全的，
  不会导致循环依赖。
"""
from typing import Any, Protocol, cast

from .manager import LogManager

__all__ = ["logger"]


class LoggingProxy(Protocol):
    """logger 对外暴露的静态类型接口。

    使 pyright 能推断 `logger.error(...)` 等调用的返回类型为 None，
    避免退化为 Any（reportAny）。
    """

    def info(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def error(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def trace(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def success(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None: ...
    def log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None: ...
    def bind(self, *args: Any, **kwargs: Any) -> Any: ...


class _LazyLogger:
    """惰性日志代理：延迟到首次使用时才解析底层 logger。

    显式声明日志方法签名（返回 None），使静态类型检查器（pyright 等）
    能推断 `logger.error(...)` 等调用的类型，而不是退化为 Any。
    """

    def __init__(self) -> None:
        self._resolved: (Any) | None = None
        self._resolving: bool = False

    def _resolve(self) -> Any:
        """解析并缓存底层 logger 实现。"""
        if self._resolved is None:
            # 若正在解析过程中（极端递归场景），返回空代理避免死循环
            if self._resolving:
                return _NullLogger()
            self._resolving = True
            try:
                self._resolved = LogManager.get_logger()
            finally:
                self._resolving = False
        return self._resolved

    def __getattr__(self, name: str) -> Any:
        # 将未显式声明的属性/方法委托给底层实现
        return getattr(self._resolve(), name)

    # ---- 显式日志方法签名（返回 None，消除 reportAny） ----

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().info(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().error(message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().debug(message, *args, **kwargs)

    def trace(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().trace(message, *args, **kwargs)

    def success(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().success(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().warning(message, *args, **kwargs)

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().exception(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().critical(message, *args, **kwargs)

    def log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        self._resolve().log(level, message, *args, **kwargs)

    def bind(self, *args: Any, **kwargs: Any) -> Any:
        return self._resolve().bind(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<LazyLogger resolved={self._resolved is not None}>"


class _NullLogger:
    """空日志器：极端递归场景下的安全降级，避免无限递归。"""

    def __getattr__(self, name: str) -> Any:
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


# 全局惰性日志实例（首次使用时才真正初始化）
# 静态类型声明为 LoggingProxy（Protocol），使 logger.error(...) 等返回 None 而非 Any
logger: LoggingProxy = cast(LoggingProxy, _LazyLogger())
