"""
规则引擎合约接口
定义规则引擎的标准接口
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class EvaluationResult(Enum):
    """评估结果枚举"""
    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"  # 不表态


class IRule(ABC):
    """规则接口"""

    @abstractmethod
    async def evaluate(self, user_id: Any, resource: str, action: str, context: dict[str, Any]) -> EvaluationResult:
        """
        评估规则
        
        Args:
            user_id: 用户ID
            resource: 资源
            action: 动作
            context: 上下文信息
            
        Returns:
            EvaluationResult: 规则评估结果
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取规则名称"""
        pass


class IRuleEngine(ABC):
    """规则引擎接口"""

    @abstractmethod
    async def evaluate(self, user_id: Any, resource: str, action: str, context: dict[str, Any] | None = None) -> bool:
        """
        评估权限
        
        Args:
            user_id: 用户ID
            resource: 资源
            action: 动作
            context: 上下文信息
            
        Returns:
            bool: 是否允许
        """
        pass


class IRuleProvider(ABC):
    """规则提供者接口"""

    @abstractmethod
    async def get_rules_for_resource(self, resource: str) -> list[IRule]:
        """
        获取指定资源的规则
        
        Args:
            resource: 资源
            
        Returns:
            list[IRule]: 规则列表
        """
        pass
