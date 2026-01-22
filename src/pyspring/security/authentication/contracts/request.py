"""
认证请求模型

包含登录请求等Pydantic模型定义
"""
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, model_validator


class LoginRequest(BaseModel):
    """
    登录请求模型
    
    user_id 和 email 二选一作为登录凭证
    """
    user_id: Optional[str] = Field(default=None, description="用户唯一标识")
    email: Optional[EmailStr] = Field(default=None, description="用户邮箱")
    password: str = Field(..., min_length=6, description="用户密码")

    @model_validator(mode='after')
    def check_user_id_or_email(self):
        """验证 user_id 和 email 至少提供一个"""
        if not self.user_id and not self.email:
            raise ValueError("必须提供 user_id 或 email 其中之一")
        return self


__all__ = ['LoginRequest']
