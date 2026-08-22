from typing import Any

from loguru import logger as _loguru
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.log.core.interface import ILoggerService


class _BoundLogger(ILoggerService):
    """一个轻量代理：在调用时同时应用深度定位与绑定的 extra"""

    def __init__(self, base_service: "LoguruService", extra: dict[str, Any]):
        self._base = base_service
        self._extra = dict(extra or {})

    def _opt_bind(self):
        # 通过公共方法避免访问受保护成员
        return self._base.with_context(**self._extra)

    def info(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().info(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().debug(message, *args, **kwargs)

    def trace(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().trace(message, *args, **kwargs)

    def success(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().success(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().warning(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().exception(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().critical(message, *args, **kwargs)

    def log(self, level: int, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().log(level, message, *args, **kwargs)

    def bind(self, *args, **kwargs) -> Any:
        new_extra = dict(self._extra)
        new_extra.update(kwargs or {})
        return _BoundLogger(self._base, new_extra)


@Component
@Singleton
class LoguruService(IManaged, ILoggerService):
    """Loguru 日志服务（由IOC容器管理单例）"""

    _configured = False

    def __init__(self):
        """初始化日志服务"""
        self._setup_logging()

    def _setup_logging(self):
        """从配置文件设置日志"""
        from ..setup import ConfiguratorFacade

        # 使用新的ConfiguratorFacade统一配置入口
        ConfiguratorFacade.setup(force=False)

    def _opt(self):
        """固定 depth=1：精准定位到调用 LoguruService/BoundLogger 的直接业务调用点。
        动态扫描在复杂调用链下易越级，导致文件/行号跳转不一致，故改为稳定策略。
        """
        return _loguru.opt(depth=1)

    def with_context(self, **extra) -> Any:
        return self._opt().bind(**(extra or {}))

    def info(self, message: str, *args, **kwargs) -> Any:
        return self._opt().info(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> Any:
        return self._opt().error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> Any:
        return self._opt().debug(message, *args, **kwargs)

    def trace(self, message: str, *args, **kwargs) -> Any:
        return self._opt().trace(message, *args, **kwargs)

    def success(self, message: str, *args, **kwargs) -> Any:
        return self._opt().success(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> Any:
        return self._opt().warning(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> Any:
        return self._opt().exception(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> Any:
        return self._opt().critical(message, *args, **kwargs)

    def log(self, level: int, message: str, *args, **kwargs) -> Any:
        return self._opt().log(level, message, *args, **kwargs)

    def bind(self, *args, **kwargs) -> Any:
        return _BoundLogger(self, kwargs or {})
