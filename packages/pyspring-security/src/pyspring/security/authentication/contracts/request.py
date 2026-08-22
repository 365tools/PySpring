"""
认证请求模型

包含登录请求等Pydantic模型定义
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    登录请求模型

    使用统一的 identifier 字段作为登录凭证，可以是：
    - 用户名（username）
    - 邮箱（email）
    - 用户ID（user_id）
    - 手机号（phone）
    - 其他配置的字段

    框架会根据 config/security.yaml 中的 identifier_fields 配置自动匹配
    """

    identifier: str = Field(..., description="登录标识符（用户名/邮箱/手机号等）")
    password: str = Field(..., min_length=6, description="用户密码")


__all__ = ["LoginRequest"]
