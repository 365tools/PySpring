"""
Token 生成策略接口

定义不同类型的 Token 生成器（JWT、Session、API Key 等）
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ITokenGenerator(ABC):
    """
    Token 生成器策略接口
    
    【设计目的】
    - 解决 Token 生成逻辑固定为 JWT 的问题
    - 支持多种 Token 类型（JWT、Session、API Key、OAuth2）
    - 与 IRequestAuthenticationProvider 对称设计
    
    【实现示例】
    - JWTTokenGenerator: 生成 JWT Token
    - SessionTokenGenerator: 生成 Session ID
    - APIKeyTokenGenerator: 生成 API Key
    """

    @abstractmethod
    def generate_access_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """
        生成访问令牌
        
        Args:
            data: Token 载荷数据
            expires_delta: 过期时间增量（可选）
            
        Returns:
            str: 访问令牌字符串
        """
        pass

    @abstractmethod
    async def generate_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """
        生成刷新令牌
        
        Args:
            data: Token 载荷数据
            expires_delta: 过期时间增量（可选）
            
        Returns:
            str: 刷新令牌字符串
        """
        pass

    @abstractmethod
    async def parse_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        解析令牌
        
        Args:
            token: 令牌字符串
            token_type: 令牌类型（access/refresh）
            
        Returns:
            Optional[Dict]: 令牌载荷数据，解析失败返回 None
        """
        pass

    @abstractmethod
    def get_token_type(self) -> str:
        """
        获取 Token 类型标识
        
        Returns:
            str: Token 类型（jwt、session、api_key 等）
        """
        pass

    @abstractmethod
    def get_access_token_expire(self) -> int:
        """
        获取访问令牌过期时间
        
        Returns:
            int: 过期时间（秒）
        """
        pass

    @abstractmethod
    def get_refresh_token_expire(self) -> int:
        """
        获取刷新令牌过期时间
        
        Returns:
            int: 过期时间（秒）
        """
        pass
