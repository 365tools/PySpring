from typing import Optional

from fastapi import HTTPException, status
from fastapi_users.password import PasswordHelper
from sqlalchemy import select

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.core.services.system import SystemService
from pyspring.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authorization.rabc.orm.tables import UserTable, RoleTable, UserRoleTable, PermissionTable, RolePermissionTable
from pyspring.security.authorization.rabc.schema.constant import RevokeTokenReason
from pyspring.security.authorization.rabc.schema.requests import UserInfo, User, Role, LoginRequest, Permission
from pyspring.security.authorization.rabc.schema.response import LoginResponse, TokenResponse, LogoutResponse
from .token import TokenManagerService
from ..core.context import SecurityContextManagerService


class LoginService(ISingletonService):
    """
    登录认证服务
    
    负责用户登录、登出、获取当前用户等业务逻辑
    依赖 TokenManagerService 进行 token 管理
    """

    def __init__(self, db: DBManagerService, system_service: SystemService,
                 token_manager: TokenManagerService, context_manager: SecurityContextManagerService):
        """
        初始化登录服务
        
        Args:
            db: 数据库管理服务
            system_service: 系统配置服务
            token_manager: Token管理服务
            context_manager: 安全上下文管理器
        """
        self.db = db
        self.system = system_service
        self.token_manager = token_manager
        self.context_manager = context_manager
        self.password_helper = PasswordHelper()
        logger.info("🔧 LoginService 初始化完成 (Context Aware)")

    async def login(self, request: LoginRequest) -> LoginResponse:
        """
        用户登录

        Args:
            request: 登录凭据

        Returns:
            LoginResponse: 包含 access_token 等信息的对象

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

                # ==================== 安全上下文验证 (Context Validation) ====================
                # 使用 SecurityContextManager 调用所有验证器 (Context Policies)
                context_data = {
                    "user": db_user,
                    "request_payload": request,
                    # 如果有 raw request (fastapi.Request), 也可以在这里传入 "request": raw_request
                }

                evaluation = await self.context_manager.evaluate(context_data)

                if not evaluation.is_valid:
                    error_msg = "; ".join(evaluation.errors)
                    logger.warning(f"Login blocked by security policy: {error_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Security Policy Violation: {error_msg}"
                    )

                # 获取警告信息
                warning_msg = "; ".join(evaluation.warnings) if evaluation.warnings else ""

                # 查询用户角色
                stmt = select(RoleTable).join(
                    UserRoleTable, UserRoleTable.role_id == RoleTable.id
                ).where(UserRoleTable.user_id == db_user.id)
                result = await session.execute(stmt)
                roles = result.scalars().all()
                role_codes = [role.code for role in roles]

                # [Permission-Upgrade] 查询 RBAC 权限
                permissions = []
                if role_codes:
                    stmt = select(PermissionTable.code).join(
                        RolePermissionTable, RolePermissionTable.permission_code == PermissionTable.code
                    ).where(RolePermissionTable.role_code.in_(role_codes))
                    result = await session.execute(stmt)
                    permissions = list(set(result.scalars().all()))

                    # [安全策略]撤销该用户所有旧的Refresh Token(颁发新token, 旧的失效)
                await self.token_manager.revoke_user_refresh_tokens(
                    session,
                    db_user.id,
                    reason=RevokeTokenReason.USER_LOGIN
                )

                # 1. 准备 Access Token Payload
                token_payload = {
                    "sub": str(db_user.id),
                    "email": db_user.email,
                    "user_id": db_user.user_id,
                    "roles": role_codes,
                    "permissions": permissions,
                }

                # [增强] 动态注入 Context Claims (支持角色和权限合并)
                claims_to_merge = evaluation.claims.copy()

                if 'roles' in claims_to_merge:
                    extra_roles = claims_to_merge.pop('roles')
                    if isinstance(extra_roles, list):
                        # 合并 DB 角色和动态角色，并去重
                        token_payload['roles'] = list(set(token_payload['roles'] + extra_roles))
                        logger.debug(f"➕ 合并动态角色: {extra_roles}")

                if 'permissions' in claims_to_merge:
                    extra_perms = claims_to_merge.pop('permissions')
                    if isinstance(extra_perms, list):
                        token_payload['permissions'] = list(set(token_payload['permissions'] + extra_perms))
                        logger.debug(f"➕ 合并动态权限: {extra_perms}")

                token_payload.update(claims_to_merge)

                access_token = self.token_manager.create_access_token(data=token_payload)

                # 2. 准备 Refresh Token Payload
                refresh_token_payload = {
                    "sub": str(db_user.id),
                    "email": db_user.email,
                    "user_id": db_user.user_id,
                }
                # 注入其他动态 Claims (不包含 roles，保持 Refresh Token精简)
                refresh_token_payload.update(claims_to_merge)

                refresh_token = await self.token_manager.create_refresh_token(
                    data=refresh_token_payload
                )

                logger.info(f"✅ 用户登录成功: {db_user.email} (ID: {db_user.id})")

                # 返回登录信息
                return LoginResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    token_type="bearer",
                    expires_in=self.system.get().authentication.jwt.access_token_expire,
                    message=warning_msg if warning_msg else "登录成功"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 登录失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"登录失败: {str(e)}"
            )

    async def logout(self, token: str) -> LogoutResponse:
        """
        用户登出
        
        撤销 token 使其失效

        Args:
            token: JWT access token

        Returns:
            LogoutResponse: 登出结果

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

            return LogoutResponse(
                message="登出成功",
                detail="Token已失效"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 登出失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"登出失败: {str(e)}"
            )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        刷新访问 token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            TokenResponse: 新的 access token 信息
            
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

            return TokenResponse(
                access_token=new_access_token,
                token_type="bearer",
                expires_in=self.system_service.get().authentication.jwt.access_token_expire
            )
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

                # 查询权限
                permissions = []
                if roles:
                    role_codes = [role.code for role in roles]
                    stmt = select(PermissionTable).join(
                        RolePermissionTable, RolePermissionTable.permission_code == PermissionTable.code
                    ).where(RolePermissionTable.role_code.in_(role_codes))
                    result = await session.execute(stmt)

                    # 去重 (SQLAlchemy distinct 可能更优，这里简单使用 dict)
                    perm_map = {p.code: p for p in result.scalars().all()}
                    permissions = [Permission.model_validate(p) for p in perm_map.values()]

                return UserInfo(
                    user=user,
                    roles=roles if roles else None,
                    permissions=permissions if permissions else None
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
