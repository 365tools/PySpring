"""
日志配置管理器
从 YAML 文件加载日志配置
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.interfaces.core import IManaged
from pyspring.log.core.config import LoggingConfig
from pyspring.utils.config.finder import find_config_file


@Component()
@Singleton
class LoggingConfigManager(IManaged):
    """
    日志配置管理器（由IOC容器管理单例）
    
    负责从 YAML 文件加载日志配置
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
        
        优先级：
        1. 用户项目配置: 当前工作目录 > 项目根目录
        2. 框架默认配置: pyspring/templates/config/logging.yaml
        3. 硬编码默认配置: 基于 LoggingConfig Pydantic 模型
        
        Returns:
            配置字典
        """
        # 1. 尝试加载用户配置文件
        config_path = find_config_file('logging.yaml')

        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    self._loaded_config_path = str(config_path)
                    return config
            except Exception as e:
                print(f"❌ 加载日志配置失败: {config_path}, 错误: {e}", file=sys.stderr)

        # 2. 尝试加载框架内置的默认配置模板
        framework_config = self._load_framework_default_config()
        if framework_config:
            return framework_config

        # 3. 使用硬编码的默认配置（兜底）
        print("⚠️ 未找到日志配置文件，使用硬编码默认配置", file=sys.stderr)
        return self._get_default_config()

    def _load_framework_default_config(self) -> Optional[Dict[str, Any]]:
        """
        加载框架内置的默认配置模板
        
        Returns:
            框架默认配置字典，如果加载失败则返回 None
        """
        try:
            # 获取 pyspring 包的安装路径
            import pyspring
            package_path = Path(pyspring.__file__).parent
            template_config_path = package_path / 'templates' / 'config' / 'logging.yaml'

            if template_config_path.exists():
                with open(template_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    self._loaded_config_path = str(template_config_path)
                    print(f"✅ 使用框架默认配置: {template_config_path}", file=sys.stderr)
                    return config
        except Exception as e:
            print(f"⚠️ 加载框架默认配置失败: {e}", file=sys.stderr)

        return None

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典（基于 Pydantic 模型生成）
        """
        # 将配置转换为字典并移除 None 值
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