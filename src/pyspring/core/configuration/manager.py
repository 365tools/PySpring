"""
配置管理

提供配置管理的通用接口和实现。
完全通用，使用泛型支持任何配置类型。
"""
import os
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic, cast

from pydantic_settings import BaseSettings

from pyspring.log.instance import logger
from .loader import ConfigLoader
from ..abstracts.interfaces.ISingleton import ISingletonService

TSettings = TypeVar('TSettings', bound=BaseSettings)


class BaseConfigManager(ISingletonService, ABC, Generic[TSettings]):
    """
    配置管理器基类（。IoC 容器管理单例。
    
    提供配置加载、缓存、重载等通用功能
    使用泛型支持任何类型的配置类。
    """

    _settings: Optional[TSettings] = None

    def __init__(self):
        """初始化配置管理器"""
        if self._settings is None:
            self.loader = ConfigLoader()
            self._load_config()

    @abstractmethod
    def _create_settings(self) -> TSettings:
        """
        创建Settings实例
        
        子类必须实现此方法，返回具体的配置类实例
        
        Returns:
            TSettings: 配置实例
        """
        pass

    def _load_config(self):
        """
        加载配置
        
        按标准顺序加载所有配置源
        """
        try:
            # 使用loader加载所有配置源
            self.loader.load_all()

            # 创建Settings实例
            self._settings = self._create_settings()

            logger.debug("✅ 配置加载完成")
        except Exception as e:
            logger.error(f"✅ 配置加载失败: {e}")
            raise

    @property
    def settings(self) -> TSettings:
        """
        获取配置实例
        
        Returns:
            TSettings: 配置实例
        """
        if self._settings is None:
            self._load_config()
        return cast(TSettings, self._settings)

    def reload(self):
        """重新加载配置"""
        logger.info("🔄 重新加载配置...")
        self._settings = None
        self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """
        使用点号路径获取配置
        
        例如果
            manager.get("database.type")
            manager.get("app.server.port")
        
        Args:
            key: 配置键（点号分隔
            default: 默认。
            
        Returns:
            Any: 配置
        """
        keys = key.split(".")
        value = self.settings

        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value

    def set_env(self, key: str, value: str) -> None:
        """
        设置环境变量
        
        注意：这只会影响当前进程，不会持久化
        
        Args:
            key: 环境变量
            value: 环境变量
        """
        os.environ[key] = value
        logger.debug(f"✅ 已设置环境变。 {key}")


__all__ = ["BaseConfigManager", "TSettings"]
