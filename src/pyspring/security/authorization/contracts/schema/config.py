"""
JWT 认证配置模型

包含 JWT 相关的配置类
"""
from pydantic import Field

from pyspring.core.abstracts.config import ConfigSection


class JWTConfig(ConfigSection):
    """JWT配置"""
    secret_key: str = Field(
        default="CHANGE_THIS_TO_A_RANDOM_SECRET_KEY_IN_PRODUCTION",
        description="JWT密钥"
    )
    algorithm: str = Field(default="HS256", description="加密算法")
    access_token_expire: int = Field(default=3600, ge=1, description="访问令牌过期时间(秒)")
    refresh_token_expire: int = Field(default=2592000, ge=1, description="刷新令牌过期时间(秒)")


class AuthenticationConfig(ConfigSection):
    """认证配置"""
    jwt: JWTConfig = Field(default_factory=JWTConfig, description="JWT配置")


__all__ = [
    "JWTConfig",
    "AuthenticationConfig",
]
