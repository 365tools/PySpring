"""
日志配置管理器
从 YAML 文件加载日志配置
使用新的三层配置架构：框架默认值 < 用户配置 < 环境变量

注意：此模块使用标准库 logging 记录诊断信息，避免污染 stderr。
"""
import logging
from typing import Any

from pyspring.core.config_manager import ConfigManager
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.log.core.config import LoggingConfig

logger = logging.getLogger(__name__)


@Component
@Singleton
class LoggingConfigManager(IManaged):
    """
    日志配置管理器（由IOC容器管理单例）
    
    负责从 YAML 文件加载日志配置
    
    配置加载顺序：
    1. 框架默认配置 (src/pyspring/config/defaults/logging.yaml)
    2. 用户项目配置 (config/logging.yaml)  # 覆盖框架默认
    3. 环境变量（如有需要）                 # 覆盖用户配置
    """

    _config: (dict[str, Any]) | None = None
    _loaded_config_path: (str) | None = None
    _initialized: bool = False

    def __init__(self):
        """初始化配置管理器"""
        if not self.__class__._initialized:
            self._config = self._load_config()
            self.__class__._initialized = True

    def _load_config(self) -> dict[str, Any]:
        """
        加载日志配置文件
        使用新的 ConfigManager 实现三层配置架构
        
        Returns:
            配置字典（框架默认值 + 用户覆盖）
        """
        try:
            # 使用 ConfigManager 加载配置（自动合并框架默认值和用户配置）
            config = ConfigManager.load_config("logging")
            self._loaded_config_path = "config/logging.yaml (with framework defaults)"
            return config
        except Exception as e:
            logger.warning("⚠️ [LoggingConfigManager] 加载配置异常，使用框架默认值: %s", e)
            # 降级到框架默认值
            return ConfigManager._load_framework_defaults("logging")

    @staticmethod
    def _get_default_config() -> dict[str, Any]:
        """
        获取默认配置（兜底方案）
        
        Returns:
            默认配置字典
        """
        return {'logging': LoggingConfig().model_dump(exclude_none=True)}

    @property
    def config(self) -> dict[str, Any] | None:
        """
        获取配置
        
        Returns:
            配置字典（未初始化时为 None）
        """
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """
        使用点号路径获取配置值
        
        例如：
            manager.get("logging.level")
            manager.get("logging.console.enabled")
        
        Args:
            key: 配置键（点号分隔）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def reload(self):
        """重新加载配置"""
        logger.debug("🔄 重新加载日志配置...")
        self._config = None
        self._config = self._load_config()
