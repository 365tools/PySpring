from typing import Any

from fastapi import HTTPException, status
from fastapi_users.password import PasswordHelper

from pyspring.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.contracts.interface.login import ILoginProvider
from pyspring.security.authentication.contracts.interface.user import IUserProvider
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

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户ID/邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. 验证密码
        verified, updated_password_hash = self.password_helper.verify_and_update(
            request.password, user.password
        )

        if not verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. 如果密码哈希需要更新（算法升级等）
        if updated_password_hash:
            # 注意：这里为了保持 Provider 的纯粹性，可能需要一个更优雅的方式来更新
            # 但为了简单起见，我们暂时直接操作 DB，或者忽略它
            # 在企业级实现中，可能有一个 UserUpdater 接口
            async with await self.db.get_session() as session:
                # 重新 attach 到 session
                session.add(user)
                user.password = updated_password_hash
                await session.commit()
                logger.info(f"🔐 Password hash updated for user {user.id}")

        return user
