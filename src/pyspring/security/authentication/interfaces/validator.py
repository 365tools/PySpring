from abc import ABC, abstractmethod
from typing import Dict, Any, List

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
    async def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证上下文
        
        Args:
            context: 上下文数据，包含 user, request 等
            
        Returns:
            Dict[str, Any]: 验证结果
            {
                "success": bool,          # 是否通过(通常为True，除非是阻断性错误)
                "reason": str,            # 错误原因/警告信息
                "claims": Dict[str, Any], # 需要写入Token的额外数据
                "warnings": List[str]     # 警告列表
            }
        """
        pass
