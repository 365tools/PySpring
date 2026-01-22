"""
请求认证提供者接口

用于验证 API 请求中的认证凭据（Token、API Key、Session 等）
与 ILoginProvider（登录认证）的区别：
- ILoginProvider: 验证登录凭据（用户名+密码）→ 生成 Token
- IRequestAuthenticationProvider: 验证请求凭据（Token、API Key）→ 放行请求
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from fastapi import Request


@dataclass
class RequestAuthenticationResult:
    """请求认证结果"""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    roles: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    provider_name: Optional[str] = None


class IRequestAuthenticationProvider(ABC):
    """
    请求认证提供者接口
    
    【使用场景】
    - 已登录用户的 API 请求验证
    - 从请求中提取并验证认证凭据
    
    【实现示例】
    - JWTRequestAuthenticationProvider: 验证 JWT Token
    - APIKeyRequestAuthenticationProvider: 验证 API Key
    - SessionRequestAuthenticationProvider: 验证 Session Cookie
    
    【与 ILoginProvider 的区别】
    - ILoginProvider: 用于获取 Token 的初始登录（验证密码、验证码等）
    - IRequestAuthenticationProvider: 用于持有 Token 后的请求验证（验证Token、API Key等）
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化请求认证提供者
        
        Args:
            name: 提供者名称
            config: 提供者配置
        """
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.priority = config.get("priority", 999)
        self._provider_config = config.get("config", {})

    @abstractmethod
    async def authenticate(self, request: Request) -> RequestAuthenticationResult:
        """
        执行认证逻辑
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            RequestAuthenticationResult: 认证结果
        """
        pass

    @abstractmethod
    async def extract_credentials(self, request: Request) -> Optional[Any]:
        """
        从请求中提取凭证
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            Optional[Any]: 凭证数据（如 Token、API Key 等）
        """
        pass

    @abstractmethod
    async def validate_credentials(self, credentials: Any) -> RequestAuthenticationResult:
        """
        验证凭证
        
        Args:
            credentials: 凭证数据
            
        Returns:
            RequestAuthenticationResult: 验证结果
        """
        pass

    def is_enabled(self) -> bool:
        """检查提供者是否启用"""
        return self.enabled

    def get_priority(self) -> int:
        """获取优先级（数字越小优先级越高）"""
        return self.priority

    def get_name(self) -> str:
        """获取提供者名称"""
        return self.name

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._provider_config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value
