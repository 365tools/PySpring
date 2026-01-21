from typing import Any

from fastapi import HTTPException, status
from fastapi_users.password import PasswordHelper

from pyspring.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.contracts.login import ILoginProvider
from pyspring.security.authentication.contracts.user import IUserProvider
from pyspring.security.authorization.contracts.schema.requests import LoginRequest


class DefaultPasswordLoginProvider(ILoginProvider):
    """
    Default Authentication Provider: Base on Password
    """

    def __init__(self, user_provider: IUserProvider, db: DBManagerService):
        self.user_provider = user_provider
        self.db = db  # 需要 DB 来更新密码哈希（如果需要升级）
        self.password_helper = PasswordHelper()

    def supports(self, request: Any) -> bool:
        return isinstance(request, LoginRequest)

    async def authenticate(self, request: Any) -> Any:
        # 0. 类型检查
        if not isinstance(request, LoginRequest):
            raise TypeError(f"DefaultPasswordLoginProvider only supports LoginRequest, got {type(request)}")

        # 1. 查找用户
        identity = request.user_id if request.user_id else request.email
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供 user_id 或 email"
            )

        user = await self.user_provider.get_user_by_identity(identity)

        # 2. 验证密码（防时序攻击：无论用户是否存在，都执行相同的哈希操作）
        verified = False
        updated_password_hash = None

        if user:
            # 用户存在：验证真实密码
            verified, updated_password_hash = self.password_helper.verify_and_update(
                request.password, user.password
            )
        else:
            # 用户不存在：执行dummy hash以保持恒定时间
            # 使用有效的bcrypt哈希（"dummy_password"的哈希值）
            # 这确保验证时间与真实验证相近，防止时序攻击
            dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNd.OwVgKi"
            try:
                self.password_helper.verify_and_update(request.password, dummy_hash)
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

        # 4. 如果密码哈希需要更新（算法升级等）
        if updated_password_hash:
            # 使用悲观锁防止并发更新导致数据丢失
            async with await self.db.session() as session:
                from sqlalchemy import select

                # 使用 select_for_update 加锁
                stmt = select(self.user_provider.component.user_orm_model).where(
                    self.user_provider.component.user_orm_model.id == user.id
                ).with_for_update()

                result = await session.execute(stmt)
                locked_user = result.scalar_one_or_none()

                if locked_user:
                    locked_user.password = updated_password_hash
                    await session.commit()
                    logger.info(f"[Security] Password hash updated for user {user.id}")

        return user
