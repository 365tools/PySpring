from typing import Type, Optional

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.log.core.interface import ILoggerService
from pyspring.log.providers.loguru.services.service import LoguruService


class LogManager(ISingletonService):
    """
    日志管理器 - 负责管理日志服务的具体实现。
    允许在运行时或配置阶段切换底层的日志实现（如 Loguru, Python logging, Structlog 等）。
    """
    _implementation: Optional[ILoggerService] = None
    # 默认使用 Loguru 实现
    _provider_cls: Type[ILoggerService] = LoguruService

    @classmethod
    def set_provider(cls, provider_cls: Type[ILoggerService]):
        """
        设置日志服务提供者类
        :param provider_cls: 实现了 ILoggerService 的类
        """
        cls._provider_cls = provider_cls
        # 重置实例，以便下次调用 get_logger 时重新创建
        cls._implementation = None

    @classmethod
    def get_logger(cls) -> ILoggerService:
        """
        获取当前配置的日志服务实例
        """
        if cls._implementation is None:
            # 实例化提供者
            # 注意: 如果提供者也是 ISingletonService，理论上应该由 IoC 容器管理
            # 但作为日志这一基础服务，通常需要在 IoC 启动前就可用
            cls._implementation = cls._provider_cls()
        return cls._implementation

    @classmethod
    def reset(cls):
        """重置管理器状态 (主要用于测试)"""
        cls._implementation = None
