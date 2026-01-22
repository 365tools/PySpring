from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

from pyspring.ioc.interfaces.core import IManaged


class ITokenPayloadBuilder(IManaged, ABC):
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


class ITokenGenerator(ABC):
    """
    Token 生成器策略接口（纯策略层）
    
    职责：只负责Token的编码和解码，不涉及业务逻辑
    与ITokenService的区别：
    - ITokenGenerator: 策略层（encode/decode、不同算法实现）
    - ITokenService: 服务层（编排、黑名单、存储、验证）
    
    支持的实现：
    - JWTTokenGenerator: JWT算法实现
    - SessionTokenGenerator: Session实现  
    - APIKeyTokenGenerator: API Key实现
    """

    @abstractmethod
    def encode(self, payload: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """
        编码Token
        
        Args:
            payload: Token载荷数据
            expires_delta: 过期时间增量（可选）
            
        Returns:
            str: 编码后的Token字符串
        """
        pass

    @abstractmethod
    def decode(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码Token
        
        Args:
            token: Token字符串
            
        Returns:
            Optional[Dict]: 解码后的载荷，失败返回None
        """
        pass

    @abstractmethod
    def get_token_type(self) -> str:
        """
        获取Token类型标识
        
        Returns:
            str: Token类型（jwt、session、api_key等）
        """
        pass

    @abstractmethod
    def get_access_token_expire(self) -> int:
        """获取访问令牌默认过期时间（秒）"""
        pass

    @abstractmethod
    def get_refresh_token_expire(self) -> int:
        """获取刷新令牌默认过期时间（秒）"""
        pass


class ITokenService(IManaged, ABC):
    """
    Token 服务接口（服务层）
    
    职责：Token生命周期管理、黑名单、存储、验证
    依赖：ITokenGenerator（委托编码/解码）
    """

    @property
    @abstractmethod
    def token_generator(self) -> 'ITokenGenerator':
        """获取 Token 生成器"""
        pass

    @abstractmethod
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """创建 Access Token"""
        pass

    @abstractmethod
    async def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
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
