"""
认证工具函数

从中间件注入的请求状态中获取用户信息
"""
from typing import Optional, List

from fastapi import Request, HTTPException, status


class AuthUtils:
    """
    认证工具类
    """

    @staticmethod
    def get_current_user_id(request: Request) -> int:
        """
        从请求状态中获取当前用户ID

        Args:
            request: FastAPI请求对象

        Returns:
            用户ID

        Raises:
            HTTPException: 如果未找到用户ID（不应该发生，因为中间件已验证）
        """
        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未找到用户信息，请重新登录"
            )
        return user_id

    @staticmethod
    def get_current_user_email(request: Request) -> Optional[str]:
        """
        从请求状态中获取当前用户邮箱

        Args:
            request: FastAPI请求对象

        Returns:
            用户邮箱，如果不存在返回None
        """
        return getattr(request.state, "user_email", None)

    @staticmethod
    def get_current_user_roles(request: Request) -> List[str]:
        """
        从请求状态中获取当前用户角色列表

        Args:
            request: FastAPI请求对象

        Returns:
            角色列表
        """
        return getattr(request.state, "user_roles", [])

    @staticmethod
    def get_token_payload(request: Request) -> dict:
        """
        从请求状态中获取Token完整载荷

        Args:
            request: FastAPI请求对象

        Returns:
            Token载荷字典
        """
        return getattr(request.state, "token_payload", {})

    @staticmethod
    def is_device_verified(request: Request) -> bool:
        """
        检查当前请求是否通过了设备验证

        Args:
            request: FastAPI请求对象

        Returns:
            是否通过设备验证
        """
        return getattr(request.state, "device_verified", False)

    @staticmethod
    def get_device_fingerprint(request: Request) -> Optional[str]:
        """
        从请求状态中获取设备指纹

        Args:
            request: FastAPI请求对象

        Returns:
            设备指纹，如果不存在返回None
        """
        return getattr(request.state, "device_fingerprint", None)

    @staticmethod
    def has_role(request: Request, role: str) -> bool:
        """
        检查当前用户是否具有指定角色

        Args:
            request: FastAPI请求对象
            role: 角色名称

        Returns:
            是否具有该角色
        """
        user_roles = AuthUtils.get_current_user_roles(request)
        return role in user_roles

    @staticmethod
    def has_any_role(request: Request, roles: List[str]) -> bool:
        """
        检查当前用户是否具有任意一个指定角色

        Args:
            request: FastAPI请求对象
            roles: 角色列表

        Returns:
            是否具有任意角色
        """
        user_roles = AuthUtils.get_current_user_roles(request)
        return any(role in user_roles for role in roles)

    @staticmethod
    def require_role(request: Request, role: str):
        """
        要求当前用户具有指定角色，否则抛出异常

        Args:
            request: FastAPI请求对象
            role: 需要的角色

        Raises:
            HTTPException: 如果用户没有该角色
        """
        if not AuthUtils.has_role(request, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"此操作需要 '{role}' 角色"
            )

    @staticmethod
    def require_any_role(request: Request, roles: List[str]):
        """
        要求当前用户具有任意一个指定角色，否则抛出异常

        Args:
            request: FastAPI请求对象
            roles: 需要的角色列表

        Raises:
            HTTPException: 如果用户没有任何所需角色
        """
        if not AuthUtils.has_any_role(request, roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"此操作需要以下角色之一: {', '.join(roles)}"
            )
