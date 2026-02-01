"""
安全上下文验证器接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class ValidationResult:
    """验证结果"""
    success: bool
    reason: Optional[str] = None
    claims: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None


class ISecurityContextValidator(ABC):
    """
    安全上下文验证器接口
    
    用于在认证过程中验证和增强上下文数据
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """验证器名称"""
        pass

    @abstractmethod
    async def validate(self, context: Dict[str, Any]) -> ValidationResult:
        """
        验证上下文
        
        Args:
            context: 上下文数据
            
        Returns:
            ValidationResult: 验证结果
        """
        pass
