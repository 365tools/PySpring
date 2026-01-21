"""
数据仓储配置管理器
从 YAML 文件加载缓存和数据库配置
"""
from typing import Dict, Any

import yaml

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.log.instance import logger
from pyspring.utils.config.finder import find_config_file


class RepositoriesConfigManager(ISingletonService):  # 仍然继承 ISingletonService，但单例由 IoC 容器管理
    """
    数据仓储配置管理器（由 IoC 容器管理单例）
    
    负责从 YAML 文件加载缓存和数据库配置
    """

    # 移除旧的单例实现细节
    # _config: Optional[Dict[str, Any]] = None
    # _instance: Optional['RepositoriesConfigManager'] = None
    # _initialized: bool = False

    # 移除 __new__ 方法
    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #     return cls._instance

    def __init__(self):
        """初始化配置管理器"""
        # 移除单例初始化检查，现在由 IoC 容器保证只初始化一次
        self._config = self._load_config()
        # logger.debug("🔧 RepositoriesConfigManager 初始化完成")


    def _load_config(self) -> Dict[str, Any]:
        """
        加载仓储配置文件
        
        优先级：当前工作目录 > 项目根目录
        
        Returns:
            配置字典，如果配置文件不存在则返回默认配置
        """
        config_path = find_config_file('repositories.yaml')

        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    # 简单打印，避免循环依赖
                    # logger.debug(f"✅ 已加载仓储配置: {config_path}")
                    return config
            except Exception as e:
                # logger.debug(f"❌ 加载仓储配置失败: {config_path}, 错误: {e}")
                print(f"⚠️ [RepositoriesConfigManager] 加载配置失败: {e}")

        # 返回默认配置
        # logger.debug("⚠️ 未找到仓储配置文件，使用默认配置")
        return self._get_default_config()

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典（手动构建，避免 Pydantic 递归）
        """
        # 手动构建默认配置，完全绕过 Pydantic 的初始化和环境变量读取
        return {
            'cache': {
                'type': 'memory',
                'redis': {
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0,
                    'pool': {'max_connections': 50}
                }
            },
            'database': {
                'postgresql': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'app_db',
                    'pool': {'size': 5}
                },
                'sqlite': {
                    'path': 'data/app.db'
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
            manager.get("cache.redis.host")
            manager.get("database.postgresql.pool.size")
        
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

    def get_cache_config(self) -> Dict[str, Any]:
        """
        获取缓存配置
        
        Returns:
            缓存配置字典
        """
        return self._config.get('cache', {})

    def get_database_config(self) -> Dict[str, Any]:
        """
        获取数据库配置
        
        Returns:
            数据库配置字典
        """
        return self._config.get('database', {})

    def get_database_initialization_config(self) -> Dict[str, Any]:
        """
        获取数据库初始化配置
        
        Returns:
            初始化配置字典，包含:
            - enabled: bool - 是否启用
            - mode: str - 模式 (incremental/full)
            - script_path: str - 脚本路径
            - auto_detect: bool - 是否自动检测
        """
        db_config = self.get_database_config()
        init_config = db_config.get('initialization', {})

        # 提供默认值
        return {
            'enabled': init_config.get('enabled', False),
            'mode': init_config.get('mode', 'incremental'),
            'script_path': init_config.get('script_path'),
            'auto_detect': init_config.get('auto_detect', True)
        }

    def reload(self):
        """重新加载配置"""
        logger.debug("🔄 重新加载仓储配置...")
        self._config = None
        self._config = self._load_config()
