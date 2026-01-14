"""
认证上下文管理器

类似 Spring Boot 的 SecurityContextHolder，用于在请求生命周期内存储和获取当前认证用户信息
"""
from contextvars import ContextVar
from typing import Optional

from pyspring.security.authorization.rabc.schema.requests import UserInfo

# 请求上下文变量（线程安全）
_current_user: ContextVar[Optional[UserInfo]] = ContextVar('current_user', default=None)
_current_token: ContextVar[Optional[str]] = ContextVar('current_token', default=None)


class AuthContext:
    """
    认证上下文管理器
    
    提供类似 Spring Security 的上下文管理功能：
    - SecurityContextHolder.getContext().getAuthentication().getPrincipal()
    对应 AuthContext.get_current_user()
    
    使用 contextvars 实现，确保在异步环境下的线程安全和请求隔离
    """

    @staticmethod
    def set_current_user(user: Optional[UserInfo]) -> None:
        """
        设置当前请求的用户信息
        
        Args:
            user: 用户信息对象
        """
        _current_user.set(user)

    @staticmethod
    def get_current_user() -> Optional[UserInfo]:
        """
        获取当前请求的用户信息
        
        Returns:
            当前用户信息，如果未认证则返回 None
            
        Example:
            # 在任何地方都可以直接获取当前用户
            user = AuthContext.get_current_user()
            if user:
                print(f"当前用户: {user.user.email}")
        """
        return _current_user.get()

    @staticmethod
    def set_current_token(token: Optional[str]) -> None:
        """
        设置当前请求的 token
        
        Args:
            token: JWT token
        """
        _current_token.set(token)

    @staticmethod
    def get_current_token() -> Optional[str]:
        """
        获取当前请求的 token
        
        Returns:
            当前 token，如果未认证则返回 None
        """
        return _current_token.get()

    @staticmethod
    def clear() -> None:
        """
        清除当前请求的认证上下文
        
        通常在请求结束时调用（中间件自动处理）
        """
        _current_user.set(None)
        _current_token.set(None)

    @staticmethod
    def is_authenticated() -> bool:
        """
        检查当前请求是否已认证
        
        Returns:
            是否已认证
        """
        return _current_user.get() is not None


__all__ = ['AuthContext']
