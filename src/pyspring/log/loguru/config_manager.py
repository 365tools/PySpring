"""
日志配置管理器
从 YAML 文件加载日志配置
"""
import sys
import yaml
from pyspring.interfaces.ISingleton import ISingletonService
from pyspring.utils.config_finder import find_config_file
from typing import Dict, Any, Optional


class LoggingConfigManager(ISingletonService):
    """
    日志配置管理器（由 IoC 容器管理单例）
    
    负责从 YAML 文件加载日志配置
    """

    _config: Optional[Dict[str, Any]] = None
    _instance: Optional['LoggingConfigManager'] = None
    _initialized: bool = False

    def __new__(cls):
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置管理器（只执行一次）"""
        if not self.__class__._initialized:
            self._config = self._load_config()
            self.__class__._initialized = True

    def _load_config(self) -> Dict[str, Any]:
        """
        加载日志配置文件
        
        优先级：当前工作目录 > 项目根目录
        
        Returns:
            配置字典，如果配置文件不存在则返回默认配置
        """
        config_path = find_config_file('logging.yaml')

        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    # 简单打印，避免循环依赖
                    print(f"✅ 已加载日志配置: {config_path}", file=sys.stderr)
                    return config
            except Exception as e:
                print(f"❌ 加载日志配置失败: {config_path}, 错误: {e}", file=sys.stderr)

        # 返回默认配置
        print("⚠️ 未找到日志配置文件，使用默认配置", file=sys.stderr)
        return self._get_default_config()

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'logging': {
                'level': 'INFO',
                'console': {
                    'enabled': True,
                    'colorize': True,
                    'format': '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[file_relative]}</cyan>:<cyan>{line}</cyan> | {message}'
                },
                'file': {
                    'enabled': False,
                    'path': 'logs/app.log',
                    'rotation': '10 MB',
                    'retention': '7 days',
                    'compression': 'zip',
                    'format': '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[file_relative]}:{line} | {message}'
                },
                'advanced': {
                    'backtrace': True,
                    'diagnose': True,
                    'enqueue': True,
                    'depth_offset': 1
                },
                'filters': {
                    'health_check': True,
                    'metrics': True,
                    'favicon': True,
                    'custom_paths': ['/health', '/metrics', '/favicon.ico']
                },
                'intercept': {
                    'stdlib': True,
                    'uvicorn': True,
                    'fastapi': True,
                    'watchfiles': True,
                    'custom_loggers': []
                }
            }
        }

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
