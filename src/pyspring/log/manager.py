"""
日志管理器
"""
from typing import Type, Optional, Dict

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.interfaces.core import IManaged
from .core.interface import ILoggerService
from .providers.loguru.services.service import LoguruService


@Component()
@Singleton
class LogManager(IManaged):
    """
    日志管理器 - 负责管理日志服务的具体实现
    
    使用新IOC框架管理生命周期
    通过配置文件自动选择日志实现，无需手动切换
    """
    _implementation: Optional[ILoggerService] = None
    _provider_registry: Dict[str, Type[ILoggerService]] = {
        "loguru": LoguruService,
        # 未来扩展: "stdlib": PythonLoggingService,
        # 未来扩展: "structlog": StructlogService,
    }
    _configured_provider: str = "loguru"  # 默认提供者

    @classmethod
    def _register_provider(cls, name: str, provider_cls: Type[ILoggerService]):
        """
        【内部方法】注册日志提供者
        
        仅供框架内部使用，不对外暴露
        
        Args:
            name: 提供者名称（如 'loguru', 'stdlib', 'structlog'）
            provider_cls: 实现了 ILoggerService 的类
        """
        cls._provider_registry[name] = provider_cls

    @classmethod
    def configure_provider(cls, provider_name: str):
        """
        【内部方法】配置日志提供者
        
        由配置管理器调用，不建议业务代码直接调用
        
        Args:
            provider_name: 提供者名称（如 'loguru', 'stdlib', 'structlog'）
        
        Raises:
            ValueError: 提供者未注册时抛出
        """
        if provider_name not in cls._provider_registry:
            raise ValueError(
                f"日志提供者 '{provider_name}' 未注册。"
                f"可用提供者: {list(cls._provider_registry.keys())}"
            )
        cls._configured_provider = provider_name
        # 重置实例，以便下次调用 get_logger 时重新创建
        cls._implementation = None

    @classmethod
    def get_logger(cls) -> ILoggerService:
        """
        获取当前配置的日志服务实例
        
        Returns:
            ILoggerService: 日志服务实例
        """
        if cls._implementation is None:
            provider_cls = cls._provider_registry[cls._configured_provider]
            cls._implementation = provider_cls()
        return cls._implementation

    @classmethod
    def reset(cls):
        """重置管理器状态（主要用于测试）"""
        cls._implementation = None