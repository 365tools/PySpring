"""
新版IOC容器管理器

全局容器的单例访问点
"""
from typing import Optional, List

from pyspring.ioc.container.container import Container


class ApplicationContext:
    """
    应用上下文（全局IOC容器）
    
    提供全局访问点，简化容器的使用。
    建议在应用启动时初始化一次，之后通过 get_instance() 获取。
    """

    _instance: Optional['ApplicationContext'] = None
    _container: Optional[Container] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, base_packages: List[str]):
        """
        初始化应用上下文
        
        Args:
            base_packages: 要扫描的包路径列表
        """
        instance = cls()
        instance._container = Container()
        instance._container.scan(base_packages)
        return instance

    @classmethod
    def get_instance(cls) -> 'ApplicationContext':
        """获取应用上下文实例"""
        if cls._instance is None or cls._instance._container is None:
            raise RuntimeError("ApplicationContext未初始化，请先调用 initialize()")
        return cls._instance

    @property
    def container(self) -> Container:
        """获取IOC容器"""
        if self._container is None:
            raise RuntimeError("Container未初始化")
        return self._container

    def get(self, name: str):
        """获取服务（快捷方法）"""
        return self.container.get(name)

    def get_by_type(self, service_type: type):
        """根据类型获取服务（快捷方法）"""
        return self.container.get_by_type(service_type)

    @classmethod
    def reset(cls):
        """重置应用上下文（主要用于测试）"""
        cls._instance = None
        cls._container = None


# 向后兼容的别名
AppContext = ApplicationContext

__all__ = ['ApplicationContext', 'AppContext']
