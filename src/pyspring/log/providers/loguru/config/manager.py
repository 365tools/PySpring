"""
日志配置管理器
从 YAML 文件加载日志配置
使用新的三层配置架构：框架默认值 < 用户配置 < 环境变量
"""
import sys
from typing import Dict, Any, Optional

from pyspring.config_manager import ConfigManager
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.interfaces.core import IManaged
from pyspring.log.core.config import LoggingConfig


@Component()
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

    _config: Optional[Dict[str, Any]] = None
    _loaded_config_path: Optional[str] = None
    _initialized: bool = False

    def __init__(self):
        """初始化配置管理器"""
        if not self.__class__._initialized:
            self._config = self._load_config()
            self.__class__._initialized = True

    def _load_config(self) -> Dict[str, Any]:
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
            print(f"⚠️  [LoggingConfigManager] 加载配置异常，使用框架默认值: {e}", file=sys.stderr)
            # 降级到框架默认值
            return ConfigManager._load_framework_defaults("logging")

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        获取默认配置（兜底方案）
        
        Returns:
            默认配置字典
        """
        return {'logging': LoggingConfig().model_dump(exclude_none=True)}

    @property
    def config(self) -> Dict[str, Any]:
        """
        获取配置
        
        Returns:
            配置字典
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
        print("🔄 重新加载日志配置...", file=sys.stderr)
        self._config = None
        self._config = self._load_config()