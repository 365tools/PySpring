"""
认证响应模型和数据结构

包含登录响应、Token响应、用户信息等Pydantic模型定义
"""
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from pyspring.core.ioc.interfaces.core import IManaged

# ==================== 数据结构模型 ====================

class User(BaseModel):
    """用户基本信息模型"""
    id: (int) | None = Field(default=None, description="数据库主键ID")
    user_id: (str) | None = Field(default=None, description="用户唯一标识")
    first_name: (str) | None = Field(default=None, description="用户名")
    last_name: (str) | None = Field(default=None, description="用户姓")
    email: (EmailStr) | None = Field(default=None, description="用户邮箱")
    password: (str) | None = Field(default=None, min_length=6, description="用户密码")
    active: bool = Field(default=True, description="用户是否激活")

    @model_validator(mode='after')
    def check_user_id_or_email(self):
        """验证 user_id 和 email 至少提供一个"""
        if not self.user_id and not self.email:
            raise ValueError("必须提供 user_id 或 email 其中之一")
        return self

    model_config = ConfigDict(from_attributes=True)


class Role(BaseModel):
    """角色模型"""
    id: (int) | None = Field(None, description="数据库主键ID")
    code: str = Field(..., description="角色代码")
    name: str = Field(..., description="角色名称")
    description: str = Field(..., description="角色描述")
    status: bool = Field(default=True, description="角色状态")

    model_config = ConfigDict(from_attributes=True)


class Permission(BaseModel):
    """权限模型"""
    id: (int) | None = Field(None, description="数据库主键ID")
    code: str = Field(..., description="权限代码")
    name: str = Field(..., description="权限名称")
    description: str = Field(..., description="权限描述")
    status: bool = Field(default=True, description="权限状态")

    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    """完整用户信息（包含角色和权限）"""
    user: User = Field(..., description="用户基本信息")
    roles: (list[Role]) | None = Field(None, description="用户角色列表")
    permissions: (list[Permission]) | None = Field(None, description="用户权限列表")

    model_config = ConfigDict(from_attributes=True)


# ==================== 响应模型 ====================

class TokenResponse(BaseModel):
    """Token响应模型（用于刷新Token）"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="有效期(秒)")


class LoginResponse(TokenResponse):
    """登录成功响应"""
    refresh_token: str = Field(..., description="刷新令牌")
    refresh_token_expire: int = Field(..., description="刷新令牌有效期(秒)")
    message: str = Field(default="登录成功", description="响应消息")
    user_info: (Any) | None = Field(default=None, description="用户信息(可选)")


class LogoutResponse(BaseModel):
    """登出响应"""
    message: str = Field(..., description="响应消息")
    detail: (str) | None = Field(None, description="详细信息")


# ==================== 接口定义 ====================

class IResponseBuilder(IManaged, ABC):
    """
    响应构建器接口
    负责构造 API 响应
    """

    @abstractmethod
    def build_login_response(self, user: Any, access_token: str, refresh_token: str, **kwargs) -> Any:
        """构造登录成功响应"""
        pass

    @abstractmethod
    def build_logout_response(self, **kwargs) -> Any:
        """构造登出响应"""
        pass

    @abstractmethod
    def build_token_response(self, access_token: str, **kwargs) -> Any:
        """构造刷新 Token 响应"""
        pass


__all__ = [
    # 数据结构
    'User', 'Role', 'Permission', 'UserInfo',
    # 响应模型
    'TokenResponse', 'LoginResponse', 'LogoutResponse',
    # 接口
    'IResponseBuilder'
]
