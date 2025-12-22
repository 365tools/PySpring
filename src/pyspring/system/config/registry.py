"""
配置注册中心

提供配置的注册、发现和管理功能
支持配置的动态注册和查询
"""
from pydantic_settings import BaseSettings
from pyspring.interfaces.ISingleton import ISingletonService
from pyspring.log.loguru.ins import logger
from typing import Dict, Type, Optional


class ConfigRegistry(ISingletonService):
    """
    配置注册中心（由 IoC 容器管理单例）
    
    管理所有已注册的配置类，支持动态查询和实例化
    """

    _registry: Dict[str, Type[BaseSettings]] = {}
    _instances: Dict[str, BaseSettings] = {}

    def register(
            self,
            name: str,
            config_class: Type[BaseSettings],
            singleton: bool = True
    ) -> None:
        """
        注册配置
        
        Args:
            name: 配置名称
            config_class: 配置
            singleton: 是否使用单例模式
        """
        if name in self._registry:
            logger.warning(f"⚠️  配置已存在，将被覆盖: {name}")

        self._registry[name] = config_class
        logger.debug(f"✅ 已注册配。 {name} -> {config_class.__name__}")

    def get_class(self, name: str) -> Optional[Type[BaseSettings]]:
        """
        获取配置
        
        Args:
            name: 配置名称
            
        Returns:
            Optional[Type[BaseSettings]]: 配置类，如果不存在则返回None
        """
        return self._registry.get(name)

    def get_instance(self, name: str, **kwargs) -> Optional[BaseSettings]:
        """
        获取配置实例
        
        如果实例不存在，则创建新实例
        
        Args:
            name: 配置名称
            **kwargs: 传递给配置类的参数
            
        Returns:
            Optional[BaseSettings]: 配置实例
        """
        # 如果已有实例，直接返。
        if name in self._instances:
            return self._instances[name]

        # 获取配置
        config_class = self.get_class(name)
        if config_class is None:
            logger.error(f"✅ 配置未注。 {name}")
            return None

        # 创建实例
        try:
            instance = config_class(**kwargs)
            self._instances[name] = instance
            logger.debug(f"✅ 已创建配置实。 {name}")
            return instance
        except Exception as e:
            logger.error(f"✅ 创建配置实例失败: {name}, 错误: {e}")
            return None

    def list_registered(self) -> list[str]:
        """
        列出所有已注册的配置名。
        
        Returns:
            list[str]: 配置名称列表
        """
        return list(self._registry.keys())

    def clear_instances(self) -> None:
        """清除所有缓存的配置实例"""
        self._instances.clear()
        logger.debug("✅ 已清除所有配置实例缓存")

    def unregister(self, name: str) -> bool:
        """
        注销配置
        
        Args:
            name: 配置名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._registry:
            del self._registry[name]
            if name in self._instances:
                del self._instances[name]
            logger.debug(f"✅ 已注销配置: {name}")
            return True
        return False


# 全局注册中心实例
registry = ConfigRegistry()

__all__ = ["ConfigRegistry", "registry"]
