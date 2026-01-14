from pathlib import Path
from typing import Dict, Any

import yaml

from pyspring.log.instance import logger


class IoCConfigLoader:
    """IoC 容器配置加载器"""

    _config_cache = None

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """
        加载 IoC 容器配置文件（带缓存）
        
        Returns:
            配置字典，如果配置文件不存在则返回默认配置
        """
        # ✅ 如果已有缓存，直接返回
        if cls._config_cache is not None:
            return cls._config_cache

        # 查找配置文件路径
        possible_paths = [
            Path.cwd() / 'config' / 'container.yaml',
            Path(__file__).parent.parent.parent.parent.parent / 'config' / 'container.yaml',  # Adjusted path for src/pyspring/ioc/core/config.py
            Path.cwd() / 'container.yaml',
        ]

        for config_path in possible_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                        logger.debug(f"✅ 已加载 IoC 容器配置: {config_path}")
                        cls._config_cache = config  # ✅ 缓存配置
                        return config
                except Exception as e:
                    logger.error(f"❌ 加载配置文件失败: {config_path}, 错误: {e}")

        # 返回默认配置
        logger.debug("⚠️ 未找到配置文件，使用默认配置")
        default_config = {
            'scan': {
                'packages': [
                    'pyspring.repositories',
                    'pyspring.security',
                    'pyspring.log',
                ],
                'recursive': True,
            },
            'logging': {
                'level': 'INFO'
            }
        }
        cls._config_cache = default_config
        return default_config
