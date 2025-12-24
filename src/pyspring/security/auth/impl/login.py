from fastapi import HTTPException, status
from fastapi_users.password import PasswordHelper
from pyspring.interfaces.ISingleton import ISingletonService
from pyspring.log.loguru.ins import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.auth.impl.device import DeviceAuthService
from pyspring.security.auth.impl.token import TokenManagerService
from pyspring.security.auth.models.rabc.orm.tables import UserTable, RoleTable, UserRoleTable
from pyspring.security.auth.models.rabc.schema.constant import RevokeTokenReason
from pyspring.security.auth.models.rabc.schema.requests import UserInfo, User, Role, LoginRequest
from pyspring.system.impl.service import SystemService
from sqlalchemy import select
from typing import Optional, Dict, Any


class LoginService(ISingletonService):
    """
    登录认证服务
    
    负责用户登录、登出、获取当前用户等业务逻辑
    依赖 TokenManagerService 进行 token 管理
    """

    def __init__(self, db: DBManagerService, system_service: SystemService, token_manager: TokenManagerService, device_auth: DeviceAuthService):
        """
        初始化登录服务
        
        Args:
            db: 数据库管理服务
            system_service: 系统配置服务
            token_manager: Token管理服务
            device_auth: 设备认证服务
        """
        self.db = db
        self.system_service = system_service
        self.token_manager = token_manager
        self.device_auth = device_auth
        self.password_helper = PasswordHelper()

    async def login(self, request: LoginRequest) -> Dict[str, Any]:
        """
        用户登录(支持设备指纹验证)

        Args:
            request: 登录凭据(包含设备指纹)

        Returns:
            包含 access_token、user_info、device_status 等信息的字典

        Raises:
            HTTPException: 认证失败
        """
        try:
            async with await self.db.get_session() as session:
                # 查找用户（根据 user_id 或 email）
                if request.user_id:
                    stmt = select(UserTable).where(UserTable.user_id == request.user_id)
                else:
                    stmt = select(UserTable).where(UserTable.email == request.email)

                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="用户ID/邮箱或密码错误",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                # 验证密码
                verified, updated_password_hash = self.password_helper.verify_and_update(
                    request.password, db_user.password
                )

                if not verified:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="邮箱或密码错误",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                # 如果密码哈希需要更新（算法升级等）
                if updated_password_hash:
                    db_user.password = updated_password_hash
                    await session.commit()

                # ==================== 设备指纹验证 ====================
                device_verification = await self.device_auth.verify_device(
                    user_id=db_user.id,
                    device_fingerprint=request.device_fingerprint
                )

                # 如果设备未注册，自动注册（待审批状态）
                if device_verification["status"] == "not_found":
                    device_name = request.device_name or "Unknown Device"
                    await self.device_auth.register_device(
                        user_id=db_user.id,
                        device_fingerprint=request.device_fingerprint,
                        device_name=device_name,
                        # requested_duration_days=request.requested_duration_days,
                        auto_approve=False  # 默认需要审批
                    )
                    logger.warning(f"⚠️ 新设备登录: {device_name} (用户: {db_user.email}), 需要审批")
                    device_verification["status"] = "pending"

                # 设备未授权或已过期, 不阻止登录但返回警告
                device_status_msg = ""
                if device_verification["status"] == "pending":
                    device_status_msg = "设备待审批, 部分功能可能受限"
                elif device_verification["status"] == "expired":
                    device_status_msg = "设备权限已过期, 请重新申请"
                    # 可以选择阻止登录或允许登录但限制功能
                    # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="设备权限已过期")

                # 查询用户角色
                stmt = select(RoleTable).join(
                    UserRoleTable, UserRoleTable.role_id == RoleTable.id
                ).where(UserRoleTable.user_id == db_user.id)
                result = await session.execute(stmt)
                roles = result.scalars().all()
                role_codes = [role.code for role in roles]

                # [安全策略]撤销该用户所有旧的Refresh Token(颁发新token, 旧的失效)
                await self.token_manager.revoke_user_refresh_tokens(
                    session,
                    db_user.id,
                    reason=RevokeTokenReason.USER_LOGIN
                )

                # 生成 JWT tokens（包含设备指纹）
                access_token = self.token_manager.create_access_token(
                    data={
                        "sub": str(db_user.id),
                        "email": db_user.email,
                        "user_id": db_user.user_id,
                        "roles": role_codes,
                        "device_fingerprint": request.device_fingerprint,  # 包含设备指纹
                        "device_authorized": device_verification["is_authorized"]  # 设备是否已授权
                    }
                )

                refresh_token = await self.token_manager.create_refresh_token(
                    data={
                        "sub": str(db_user.id),
                        "email": db_user.email,
                        "user_id": db_user.user_id,
                        "device_fingerprint": request.device_fingerprint,
                    }
                )

                logger.info(f"✅ 用户登录成功: {db_user.email} (ID: {db_user.id}), 设备状态: {device_verification['status']}")

                # 返回登录信息(包含设备状态)
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": self.system_service.get().authentication.jwt.access_token_expire,
                    "device_status": device_verification["status"],
                    "device_authorized": device_verification["is_authorized"],
                    "message": device_status_msg if device_status_msg else "登录成功"
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 登录失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"登录失败: {str(e)}"
            )

    async def logout(self, token: str) -> Dict[str, str]:
        """
        用户登出
        
        撤销 token 使其失效

        Args:
            token: JWT access token

        Returns:
            登出成功消息

        Raises:
            HTTPException: token 无效
        """
        try:
            # 验证 token（使用 TokenManagerService）
            payload = await self.token_manager.verify_token(token)

            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 无效或已过期"
                )

            # 撤销 token
            await self.token_manager.revoke_token(token)

            email = payload.get("email", "unknown")
            logger.info(f"✅ 用户登出成功: {email}")

            return {
                "message": "登出成功",
                "detail": "Token已失效"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 登出失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"登出失败: {str(e)}"
            )

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问 token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            新的 access token
            
        Raises:
            HTTPException: refresh token 无效
        """
        try:
            # 使用 TokenManagerService 刷新
            new_access_token = await self.token_manager.refresh_access_token(refresh_token)

            if not new_access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token 无效或已过期"
                )

            logger.info("✅ Token 刷新成功")

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.system_service.get().authentication.jwt.access_token_expire
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 Token 刷新失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新失败"
            )

    async def get_current_user(self, token: str) -> Optional[UserInfo]:
        """
        根据 token 获取当前用户信息
        
        Args:
            token: JWT access token
            
        Returns:
            用户信息，如果token 无效返回 None
            
        Raises:
            HTTPException: token 无效或用户不存在
        """
        try:
            # 验证 token（使✅ TokenManagerService。
            payload = await self.token_manager.verify_token(token)

            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 无效或已过期",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 获取用户ID
            user_id = int(payload.get("sub"))

            # 从数据库查询用户
            async with await self.db.get_session() as session:
                stmt = select(UserTable).where(UserTable.id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="用户不存在",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                # 构造用户信息
                user = User(
                    id=db_user.id,
                    user_id=db_user.user_id,
                    first_name=db_user.first_name,
                    last_name=db_user.last_name,
                    email=db_user.email,
                )

                # 查询角色
                stmt = select(RoleTable).join(
                    UserRoleTable, UserRoleTable.role_id == RoleTable.id
                ).where(UserRoleTable.user_id == db_user.id)
                result = await session.execute(stmt)
                roles = [Role.model_validate(role) for role in result.scalars().all()]

                return UserInfo(
                    user=user,
                    roles=roles if roles else None,
                    permissions=None,
                    device=None
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 获取当前用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证失败",
                headers={"WWW-Authenticate": "Bearer"},
            )
