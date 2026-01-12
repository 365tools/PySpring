from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class SecurityValidatorResult:
    """单个验证器的执行结果"""
    success: bool = True
    reason: str = None
    claims: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

class ISecurityContextValidator(ABC):
    """
    安全上下文验证器接口
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """验证器名称"""
        pass

    @abstractmethod
    async def validate(self, context: Dict[str, Any]) -> SecurityValidatorResult:
        """
        验证上下文
        
        Args:
            context: 上下文数据，包含 user, request 等
            
        Returns:
            SecurityValidatorResult: 验证结果对象
        """
        pass
