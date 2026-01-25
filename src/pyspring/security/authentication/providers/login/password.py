from typing import Any

from fastapi import HTTPException, status
from pyspring.ioc.annotations import ConditionalOnMissingBean
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.contracts.login import ILoginProvider
from pyspring.security.authentication.contracts.password import IPasswordEncoder
from pyspring.security.authentication.contracts.request import LoginRequest
from pyspring.security.authentication.contracts.user import IUserProvider


@ConditionalOnMissingBean  # 允许用户通过继承或创建同名类来替换
class DefaultPasswordLoginProvider(ILoginProvider):
    """
    Default Authentication Provider: Base on Password
    """

    def __init__(self, user_provider: IUserProvider, db: DBManagerService, password_encoder: IPasswordEncoder):
        self.user_provider = user_provider
        self.db = db
        self.password_encoder = password_encoder

    def supports(self, request: Any) -> bool:
        return isinstance(request, LoginRequest)

    async def authenticate(self, request: Any) -> Any:
        # 0. 类型检查
        if not isinstance(request, LoginRequest):
            raise TypeError(f"DefaultPasswordLoginProvider only supports LoginRequest, got {type(request)}")

        # 1. 查找用户（使用 identifier 字段）
        identity = request.identifier

        user = await self.user_provider.get_user_by_identity(identity)

        # 2. 验证密码（防时序攻击：无论用户是否存在，都执行相同的哈希操作）
        verified = False

        if user:
            # 用户存在：验证真实密码
            verified = self.password_encoder.verify(request.password, user.password)
        else:
            # 用户不存在：执行dummy hash以保持恒定时间
            # 使用有效的bcrypt哈希（"dummy_password"的哈希值）
            # 这确保验证时间与真实验证相近，防止时序攻击
            dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNd.OwVgKi"
            try:
                self.password_encoder.verify(request.password, dummy_hash)
            except Exception:
                pass  # 忽略dummy验证的异常
            # verified 保持 False

        # 3. 统一的认证失败响应（不泄露用户是否存在）
        if not verified or not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",  # 统一的错误消息
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

