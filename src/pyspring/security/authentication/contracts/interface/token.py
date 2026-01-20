from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


class ITokenPayloadBuilder(ISingletonService, ABC):
    """
    Token Payload 构建器接口
    负责定义 JWT Token 中包含哪些信息
    """

    @abstractmethod
    async def build_payload(self, user: Any, context_evaluation: Any = None) -> Dict[str, Any]:
        """
        构造 Token 的 Payload
        
        Args:
            user: 用户对象
            context_evaluation: 安全上下文评估结果 (可选)
            
        Returns:
            Dict: Token Payload
        """
        pass


class ITokenService(ISingletonService, ABC):
    """
    Token 服务接口
    负责 Token 的生命周期管理
    """

    @abstractmethod
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """创建 Access Token"""
        pass

    @abstractmethod
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """创建 Refresh Token"""
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证 Token"""
        pass

    @abstractmethod
    async def revoke_token(self, token: str, reason: str = "") -> bool:
        """撤销 Token"""
        pass

    @abstractmethod
    async def revoke_user_refresh_tokens(self, session: Any, user_id: Any, reason: str = "") -> None:
        """撤销用户的所有刷新令牌"""
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> str:
        """刷新 Access Token (使用 Refresh Token)"""
        pass
