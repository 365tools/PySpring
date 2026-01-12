from typing import Optional, Any

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Token响应模型 (用于刷新Token)"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="有效期(秒)")


class LoginResponse(TokenResponse):
    """登录成功响应"""
    refresh_token: str = Field(..., description="刷新令牌")
    message: str = Field(default="登录成功", description="响应消息")
    user_info: Optional[Any] = Field(default=None, description="用户信息(可选)")


class LogoutResponse(BaseModel):
    """登出响应"""
    message: str = Field(..., description="响应消息")
    detail: Optional[str] = Field(None, description="详细信息")
