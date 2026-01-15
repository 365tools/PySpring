"""
配置基类

定义配置系统的核心抽象和基类。
完全通用，不包含任何业务逻辑。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar

from pydantic import BaseModel
from pydantic_settings import BaseSettings

# 类型变量
TConfig = TypeVar('TConfig', bound=BaseSettings)


class ConfigBase(ABC):
    """
    配置基类
    
    所有配置类都应该继承此基类或使用BaseSettings
    """

    @abstractmethod
    def validate(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        pass


class ConfigSection(BaseSettings):
    """
    配置节基类
    
    所有配置节都应该继承此类
    提供Pydantic的所有功能
    """

    def validate(self) -> bool:
        """验证配置"""
        try:
            self.model_validate(self.model_dump())
            return True
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()


class ConfigMetadata(BaseModel):
    """
    配置元数据
    
    存储配置的额外信息
    """
    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    author: Optional[str] = None
    tags: list[str] = []


__all__ = [
    "ConfigBase",
    "ConfigSection",
    "ConfigMetadata",
    "TConfig",
]
