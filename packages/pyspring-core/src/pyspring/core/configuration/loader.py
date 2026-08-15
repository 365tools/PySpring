"""
配置加载。

负责从多个来源加载配置（YAML。env、环境变量）。
完全通用，不包含任何业务逻辑。
"""
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from pyspring.core.utils.config.finder import detect_project_root as _detect_root


class ConfigLoader:
    """
    通用配置加载。
    
    支持从多个来源加载配置：
    - YAML文件
    - .env文件
    - 环境变量
    """

    def __init__(self, project_root: (Path) | None = None):
        """
        初始化配置加载器
        
        Args:
            project_root: 项目根目录，如果不提供则自动检测
        """
        self.project_root = project_root or self._detect_project_root()

    def _detect_project_root(self) -> Path:
        """
        自动检测项目根目录

        复用统一的 utils.config.finder.detect_project_root，避免重复实现。
        start_from 传入本模块所在目录，保证向上查找逻辑一致。

        Returns:
            Path: 项目根目录路径
        """
        return _detect_root(Path(__file__).resolve().parent)

    def load_yaml(self, yaml_path: Path) -> dict[str, Any]:
        """
        加载YAML配置文件
        
        Args:
            yaml_path: YAML文件路径
            
        Returns:
            dict[str, Any]: 配置字典
        """
        if not yaml_path.exists():
            return {}

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                return config
        except Exception as e:
            return {}

    def load_env_files(self, env_files: list[str], override: bool = True) -> None:
        """
        按顺序加载多个.env文件
        
        Args:
            env_files: .env文件名列表（相对于project_root）
            override: 是否覆盖已存在的环境变量
        """
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                load_dotenv(env_path, override=override)

    def flatten_dict(
            self,
            d: dict[str, Any],
            parent_key: str = '',
            sep: str = '__'
    ) -> dict[str, Any]:
        """
        将嵌套字典扁平化
        
        例如：{"database": {"type": "sqlite"}} -> {"DATABASE__TYPE": "sqlite"}
        
        Args:
            d: 需要扁平化的字典
            parent_key: 父键
            sep: 分隔符
            
        Returns:
            dict[str, Any]: 扁平化后的字典
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key.upper(), str(v)))
        return dict(items)

    def merge_to_env(
            self,
            config_dict: dict[str, Any],
            override: bool = False
    ) -> None:
        """
        将配置字典合并到环境变量
        
        Args:
            config_dict: 配置字典
            override: 是否覆盖已存在的环境变量
        """
        flat_config = self.flatten_dict(config_dict)
        count = 0
        for key, value in flat_config.items():
            if override or key not in os.environ:
                os.environ[key] = str(value)
                count += 1

    def load_all(
            self,
            yaml_file: str = "config/config.yaml",
            env_files: (list[str]) | None = None,
            environment_var: str = "ENVIRONMENT",
            default_environment: str = "development"
    ) -> None:
        """
        按标准顺序加载所有配置源
        
        优先级（从低到高）：
        1. YAML配置文件
        2. .env 文件
        3. .env.{environment} 文件
            4. 环境变量（最高优先级）
            yaml_file: YAML配置文件路径
            env_files: 自定义env文件列表
            environment_var: 环境变量名称
            default_environment: 默认环境名称
        """
        # 1. 加载YAML配置
        yaml_path = self.project_root / yaml_file
        yaml_config = self.load_yaml(yaml_path)
        self.merge_to_env(yaml_config, override=False)

        # 2. 加载.env文件
        if env_files is None:
            environment = os.getenv(environment_var, default_environment)
            env_files = [".env", f".env.{environment}"]

        self.load_env_files(env_files, override=True)


__all__ = ["ConfigLoader"]
