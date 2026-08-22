"""
配置基类

定义配置系统的核心基类。
完全通用，不包含任何业务逻辑。
"""

from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic_settings import BaseSettings

# 类型变量
TConfig = TypeVar("TConfig", bound=BaseSettings)


class ConfigSection(BaseSettings):
    """
    配置节基类

    所有配置节都应该继承此类，提供Pydantic的所有功能。
    支持从 YAML 文件自动加载配置。

    配置优先级：环境变量 > YAML 文件 > Field 默认值

    使用示例：
        @Component
        @Singleton
        class CacheConfig(ConfigSection):
            model_config = SettingsConfigDict(
                yaml_config_file="config/repositories.yaml",
                yaml_config_key="cache"
            )

            type: str = Field(default="memory")
    """

    def __init__(self, **data: Any):
        """
        初始化配置节，支持 YAML 自动加载

        优先级：环境变量 > YAML > data 参数 > Field 默认值
        """
        # 获取 YAML 配置
        yaml_data = self._load_yaml_config()

        # 合并数据：YAML < data 参数
        if yaml_data:
            merged_data = {**yaml_data, **data}
        else:
            merged_data = data

        # 调用父类初始化（会处理环境变量）
        super().__init__(**merged_data)

    def _load_yaml_config(self) -> (dict[str, Any]) | None:
        """
        从 YAML 文件加载配置

        Returns:
            (dict[str, Any]) | None: YAML 配置数据，如果未配置或加载失败则返回 None
        """
        # 优先从类属性读取，然后从 model_config 读取
        yaml_file = getattr(self.__class__, "yaml_config_file", None)
        yaml_key = getattr(self.__class__, "yaml_config_key", None)

        if not yaml_file:
            # 兼容旧方式：从 model_config 读取
            model_config = getattr(self, "model_config", {})
            yaml_file = model_config.get("yaml_config_file")
            yaml_key = model_config.get("yaml_config_key")

        if not yaml_file:
            return None

        try:
            # 查找配置文件
            config_path = self._find_config_file(yaml_file)
            if not config_path or not config_path.exists():
                return None

            # 加载 YAML
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)

            # 提取指定 key
            if yaml_key:
                for key in yaml_key.split("."):
                    yaml_data = yaml_data.get(key, {})
                    if not yaml_data:
                        return None

            return yaml_data if isinstance(yaml_data, dict) else None

        except Exception:
            # 静默失败，使用默认值
            return None

    @staticmethod
    def _find_config_file(relative_path: str) -> (Path) | None:
        """
        查找配置文件（从当前目录向上搜索）

        Args:
            relative_path: 相对路径，如 "config/repositories.yaml"

        Returns:
            (Path) | None: 配置文件路径，如果未找到则返回 None
        """
        current_dir = Path.cwd()

        # 向上搜索最多 5 层
        for _ in range(5):
            config_path = current_dir / relative_path
            if config_path.exists():
                return config_path

            parent = current_dir.parent
            if parent == current_dir:
                break
            current_dir = parent

        return None

    def is_valid(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        try:
            self.model_validate(self.model_dump())
            return True
        except Exception:
            return False

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典

        Returns:
            dict[str, Any]: 配置字典
        """
        return self.model_dump()


__all__ = [
    "ConfigSection",
    "TConfig",
]
