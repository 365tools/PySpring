from typing import Any
from pyspring.log.interface import ILoggerService
from pyspring.log.manager import LogManager

class LoggerProxy(ILoggerService):
    """
    日志服务代理。
    作为全局唯一的入口，将所有日志调用转发给 LogManager 管理的具体实现。
    这允许在不修改业务代码的情况下切换日志后端。
    """

    def _impl(self) -> ILoggerService:
        """获取当前的日志实现"""
        return LogManager.get_logger()

    def info(self, message: str, *args, **kwargs) -> Any:
        return self._impl().info(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> Any:
        return self._impl().error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> Any:
        return self._impl().debug(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> Any:
        return self._impl().warning(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> Any:
        return self._impl().exception(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> Any:
        return self._impl().critical(message, *args, **kwargs)

    def log(self, level: int, message: str, *args, **kwargs) -> Any:
        return self._impl().log(level, message, *args, **kwargs)

    def bind(self, *args, **kwargs) -> Any:
        # bind 返回的是一个新的 logger 实例 (通常是 BoundLogger)
        # 我们直接透传这个行为
        return self._impl().bind(*args, **kwargs)
