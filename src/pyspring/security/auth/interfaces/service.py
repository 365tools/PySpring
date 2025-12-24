from abc import ABC, abstractmethod
from pyspring.security.auth.models.rabc.schema.requests import User
from typing import Optional


class IAuthService(ABC):
    """
    认证服务接口 (已弃用，使用FastAPI Users替代)
    """

    @abstractmethod
    async def initialize(self, *args, **kwargs) -> bool:
        """初始化服务"""
        pass

    @abstractmethod
    async def destroy(self) -> None:
        """
        销毁服务
        """
        pass

    @abstractmethod
    async def get_status(self) -> dict:
        """获取服务状态"""
        pass

    @abstractmethod
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            User: 用户对象, 验证失败时返回None
        """
        pass

    @abstractmethod
    async def create_access_token(self, data: dict, expires_delta: Optional[int] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 要编码的数据
            expires_delta: 过期时间(秒)
        Returns:
            str: JWT访问令牌
        """
        pass

    @abstractmethod
    async def get_current_user(self, token: str) -> User:
        """
        获取当前认证用户
        
        Args:
            token: JWT令牌
            
        Returns:
            User: 当前用户对象
            
        Raises:
            Exception: 当令牌无效或用户不存在时
        """
        pass

    @abstractmethod
    async def get_password_hash(self, password: str) -> str:
        """
        获取密码哈希值
        
        Args:
            password: 明文密码
            
        Returns:
            str: 哈希后的密码
        """
        pass

    @abstractmethod
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码
        
        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码
            
        Returns:
            bool: 密码是否匹配
        """
        pass
