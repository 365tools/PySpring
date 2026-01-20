from datetime import datetime, UTC
from typing import Optional, List, Any

from fastapi import HTTPException, status
from fastapi_users.password import PasswordHelper
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from pyspring.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.core.component import SecurityEntityConfiguration
from pyspring.security.authentication.core.context import AuthContext
from pyspring.security.authentication.core.interfaces import IUserManagerService, ITokenService
from pyspring.security.authorization.rabc.schema.requests import UserInfo, User, Role, Permission


class DefaultUserManagerService(IUserManagerService):
    """
    默认用户管理服务
    
    负责用户信息的查询、更新、删除等操作
    """

    def __init__(self, db: DBManagerService, token_manager: ITokenService, component: SecurityEntityConfiguration):
        """
        初始化用户管理服务
        
        Args:
            db: 数据库管理服务
            token_manager: Token 管理服务(可选, 用于获取当前用户)
            component: 安全组件配置
        """
        self.db = db
        self.token_manager = token_manager
        self.component = component
        self.password_helper = PasswordHelper()

    async def get_user_by_id(self, user_id: int) -> Optional[UserInfo]:
        """
        根据ID获取完整用户信息

        Args:
            user_id: 用户数据库ID

        Returns:
            完整用户信息, 不存在则返回None
        """
        try:
            async with await self.db.get_session() as session:
                # 查询用户基本信息
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    return None

                # 构造完整用户信息
                return await self._build_user_info(session, db_user)
        except Exception as e:
            logger.error(f"🚨 获取用户失败: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[UserInfo]:
        """
        根据邮箱获取完整用户信息

        Args:
            email: 用户邮箱

        Returns:
            完整用户信息，不存在则返回 None
        """
        try:
            async with await self.db.get_session() as session:
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.email == email)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    return None

                return await self._build_user_info(session, db_user)
        except Exception as e:
            logger.error(f"🚨 获取用户失败: {e}")
            return None

    async def get_current_user(self, token: Optional[str] = None) -> Optional[UserInfo]:
        """
        获取当前用户信息（支持两种方式）
        
        方式1: 从上下文获取（推荐，类似 Spring Boot）
            user = await user_manager.get_current_user()
            
        方式2: 传递 token
            user = await user_manager.get_current_user(token="xxx")
        
        Args:
            token: JWT access token（可选，不传则从上下文获取）
            
        Returns:
            用户信息，如果 token 无效或上下文中无用户则返回 None
            
        Raises:
            HTTPException: token 无效或用户不存在
            
        Example:
            # 方式1: 从上下文获取（推荐）
            user = await user_manager.get_current_user()
            if user:
                print(f"当前用户: {user.user.email}")
            
            # 方式2: 传递 token
            user = await user_manager.get_current_user(token=request.headers.get("Authorization"))
        """
        # 方式1: 优先从上下文获取（类似 Spring Security）
        if token is None:
            user_info = AuthContext.get_current_user()
            if user_info:
                logger.debug(f"📋 从上下文获取当前用户: {user_info.user.email}")
                return user_info

            # 上下文中没有用户信息
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证或认证已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 方式2: 通过 token 获取（兼容旧代码）
        if not self.token_manager:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TokenManager 未初始化"
            )

        try:
            # 验证 token（使用 TokenManagerService）
            payload = await self.token_manager.verify_token(token)

            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 无效或已过期",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 获取用户ID
            user_id = int(str(payload.get("sub") or 0))

            # 从数据库查询用户
            user_info = await self.get_user_by_id(user_id)

            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return user_info

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 获取当前用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证失败",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserInfo]:
        """
        获取用户列表

        Args:
            skip: 跳过的记录数
            limit: 返回的记录数限制

        Returns:
            用户信息列表
        """
        try:
            async with await self.db.get_session() as session:
                stmt = select(self.component.user_orm_model).offset(skip).limit(limit)
                result = await session.execute(stmt)
                users = result.scalars().all()

                # 构造每个用户的完整信息
                user_infos = []
                for db_user in users:
                    user_info = await self._build_user_info(session, db_user)
                    user_infos.append(user_info)

                return user_infos
        except Exception as e:
            logger.error(f"🚨 获取用户列表失败: {e}")
            return []

    async def update_user_info(self, user_id: int, user_info: UserInfo) -> UserInfo:
        """
        完整更新用户信息（包括基本信息、角色）

        Args:
            user_id: 用户数据库ID
            user_info: 完整的用户信息（包含用户、角色）

        Returns:
            更新后的完整用户信息

        Raises:
            HTTPException: 用户不存在或更新失败
        """
        try:
            async with await self.db.get_session() as session:
                # 1. 检查用户是否存在
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"用户ID {user_id} 不存在"
                    )

                # 2. 更新用户基本信息
                if user_info.user:
                    await self._update_user_basic_info(session, db_user, user_info.user)

                # 3. 更新用户角色
                if user_info.roles is not None:
                    await self._update_user_roles(session, user_id, user_info.roles)

                # 4. 提交事务
                await session.commit()
                await session.refresh(db_user)

                logger.info(f"✅ 用户信息完整更新成功: {db_user.email} (ID: {user_id})")

                # 6. 返回更新后的完整信息
                return await self._build_user_info(session, db_user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 更新用户信息失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新失败: {str(e)}"
            )

    async def update_user_field(self, user_id: int, field_name: str, field_value: Any) -> UserInfo:
        """
        更新用户的单个字段

        Args:
            user_id: 用户数据库ID
            field_name: 字段名（如 'first_name', 'email', 'password' 等）
            field_value: 字段值

        Returns:
            更新后的完整用户信息

        Raises:
            HTTPException: 用户不存在或字段不存在或更新失败
        """
        try:
            async with await self.db.get_session() as session:
                # 查询用户
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"用户ID {user_id} 不存在"
                    )

                # 验证字段是否存在
                if not hasattr(db_user, field_name):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"字段 '{field_name}' 不存在"
                    )

                # 特殊处理密码字段
                if field_name == 'password':
                    field_value = self.password_helper.hash(field_value)

                # 更新字段
                setattr(db_user, field_name, field_value)
                await session.commit()
                await session.refresh(db_user)

                logger.info(f"✅ 用户字段更新成功: {db_user.email} - {field_name}")

                return await self._build_user_info(session, db_user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 更新用户字段失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新字段失败: {str(e)}"
            )

    async def update_user_roles(self, user_id: int, roles: List[Role]) -> UserInfo:
        """
        更新用户的角色列表（替换所有角色）

        Args:
            user_id: 用户数据库ID
            roles: 新的角色列表

        Returns:
            更新后的完整用户信息

        Raises:
            HTTPException: 用户不存在或更新失败
        """
        try:
            async with await self.db.get_session() as session:
                # 检查用户是否存在
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"用户ID {user_id} 不存在"
                    )

                # 更新角色
                await self._update_user_roles(session, user_id, roles)
                await session.commit()

                logger.info(f"✅ 用户角色更新成功: {db_user.email}")

                return await self._build_user_info(session, db_user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 更新用户角色失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新角色失败: {str(e)}"
            )

    async def delete_user(self, user_id: int) -> bool:
        """
        删除用户（级联删除角色关联）

        Args:
            user_id: 用户数据库ID

        Returns:
            是否成功删除

        Raises:
            HTTPException: 用户不存在或删除失败
        """
        try:
            async with await self.db.get_session() as session:
                # 查询用户
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"用户ID {user_id} 不存在"
                    )

                # 删除用户角色关联
                stmt = delete(self.component.user_role_orm_model).where(self.component.user_role_orm_model.user_id == user_id)
                await session.execute(stmt)

                # 删除用户
                await session.delete(db_user)
                await session.commit()

                logger.info(f"✅ 用户删除成功: {db_user.email} (ID: {user_id})")
                return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 删除用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除失败: {str(e)}"
            )

    # ==================== 私有辅助方法 ====================

    async def _build_user_info(self, session: AsyncSession, db_user: Any) -> UserInfo:
        """
        构造完整的用户信息
        
        Args:
            session: 数据库会话
            db_user: 用户数据库对象 (Any to support custom models)
            
        Returns:
            完整的用户信息
        """

        # 构造用户基本信息（不返回密码）
        user = User(
            id=db_user.id,
            user_id=getattr(db_user, 'user_id', None),
            first_name=getattr(db_user, 'first_name', None),
            last_name=getattr(db_user, 'last_name', None),
            email=getattr(db_user, 'email', None),
            is_active=getattr(db_user, 'is_active', True),
        )

        # 查询用户角色
        stmt = select(self.component.role_orm_model).join(
            self.component.user_role_orm_model, self.component.user_role_orm_model.role_id == self.component.role_orm_model.id
        ).where(self.component.user_role_orm_model.user_id == db_user.id)
        result = await session.execute(stmt)
        roles = [Role.model_validate(role) for role in result.scalars().all()]

        # 查询用户权限(通过角色)
        permissions = []
        if roles:
            # 获取所有角色的 role_code
            role_codes = [role.code for role in roles]

            # 查询这些角色关联的所有权限
            stmt = select(self.component.permission_orm_model).join(
                self.component.role_permission_orm_model, self.component.role_permission_orm_model.permission_code == self.component.permission_orm_model.code
            ).where(self.component.role_permission_orm_model.role_code.in_(role_codes)).distinct()

            result = await session.execute(stmt)
            permissions = [Permission.model_validate(perm) for perm in result.scalars().all()]

        return UserInfo(
            user=user,
            roles=roles or None,
            permissions=permissions or None
        )

    async def _update_user_basic_info(self, session: AsyncSession, db_user: Any, user: User) -> None:
        """
        更新用户基本信息
        
        Args:
            session: 数据库会话
            db_user: 用户数据库对象
            user: 新的用户信息
            
        Raises:
            HTTPException: 邮箱已被占用
        """
        # 只更新明确设置的字段
        update_fields = user.model_dump(exclude_unset=True, exclude={'id'})

        # 如果更新了邮箱，检查唯一性
        if 'email' in update_fields and update_fields['email'] != db_user.email:
            stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.email == update_fields['email'])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"邮箱 {update_fields['email']} 已被使用"
                )

        # 特殊处理密码
        if 'password' in update_fields and update_fields['password']:
            update_fields['password'] = self.password_helper.hash(update_fields['password'])

        # 更新字段
        for field, value in update_fields.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)

        # 更新时间
        db_user.modifier = "system"
        db_user.modified_time = datetime.now(UTC)

    @staticmethod
    async def _update_user_roles(self, session: Any, user_id: int, roles: List[Role]) -> None:
        """
        更新用户角色（替换所有角色）
        
        Args:
            session: 数据库会话
            user_id: 用户数据库ID
            roles: 新的角色列表
        """
        # 删除现有角色关联
        stmt = delete(self.component.user_role_orm_model).where(self.component.user_role_orm_model.user_id == user_id)
        await session.execute(stmt)

        # 添加新角色
        for role in roles:
            # 查找角色
            stmt = select(self.component.role_orm_model).where(self.component.role_orm_model.code == role.code)
            result = await session.execute(stmt)
            db_role = result.scalar_one_or_none()

            if not db_role:
                logger.warning(f"⚠️ 角色不存在: {role.code}, 跳过分配")
                continue

            # 创建关联
            user_role = self.component.user_role_orm_model(user_id=user_id, role_id=db_role.id)
            session.add(user_role)
