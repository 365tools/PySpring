"""
用户管理服务

提供用户信息的查询、更新、删除等操作
使用最新的IOC和日志框架
"""
from datetime import datetime, UTC
from typing import Optional, List, Any

from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from pyspring.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.authentication.contracts.password import IPasswordEncoder
from pyspring.security.authentication.contracts.response import UserInfo, User, Role, Permission
from pyspring.security.authentication.contracts.token import ITokenService
from pyspring.security.authentication.contracts.user import IUserManagerService
from pyspring.security.authentication.infrastructure.context import AuthContext


class DefaultUserManagerService(IUserManagerService):
    """
    默认用户管理服务
    
    职责：
    - 用户信息的CRUD操作
    - 用户角色管理
    - 当前用户上下文获取
    """

    def __init__(self,
                 db: DBManagerService,
                 component: SecurityEntityConfiguration,
                 token_manager: ITokenService,
                 password_encoder: IPasswordEncoder):
        """
        初始化用户管理服务
        
        Args:
            db: 数据库管理服务
            component: 安全组件配置
            token_manager: Token管理服务（通过IOC注入）
            password_encoder: 密码编码器（通过IOC注入）
        """
        self.db = db
        self.component = component
        self.token_manager = token_manager
        self.password_encoder = password_encoder

    async def get_user_by_id(self, user_id: str) -> Optional[UserInfo]:
        """
        根据用户UUID获取完整用户信息

        Args:
            user_id: 用户UUID

        Returns:
            完整用户信息，不存在则返回None
        """
        try:
            async with await self.db.session() as session:
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.user_id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    return None

                return await self._build_user_info(session, db_user)
        except Exception as e:
            logger.error(f"[Error] 获取用户失败: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[UserInfo]:
        """
        根据邮箱获取完整用户信息

        Args:
            email: 用户邮箱

        Returns:
            完整用户信息，不存在则返回None
        """
        try:
            async with await self.db.session() as session:
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.email == email)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    return None

                return await self._build_user_info(session, db_user)
        except Exception as e:
            logger.error(f"[Error] 获取用户失败: {e}")
            return None

    async def get_current_user(self, token: Optional[str] = None) -> Optional[UserInfo]:
        """
        获取当前用户信息（支持两种方式）
        
        方式1：从上下文获取（推荐，类似Spring Security）
            user = await user_manager.get_current_user()
            
        方式2：传递token
            user = await user_manager.get_current_user(token="xxx")
        
        Args:
            token: JWT access token（可选，不传则从上下文中获取）
            
        Returns:
            用户信息，如果token无效或上下文中无用户则返回None
            
        Raises:
            HTTPException: token无效或用户不存在
        """
        # 方式1：优先从上下文获取（类似Spring Security）
        if token is None:
            user_info = AuthContext.get_current_user()
            if user_info:
                logger.debug(f"[Debug] 从上下文获取当前用户: {user_info.user.email}")
                return user_info

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证或认证已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 方式2：从token获取
        try:
            payload = await self.token_manager.verify_token(token)

            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token无效或已过期",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 输入验证：确保user_id是有效的整数
            user_id_raw = payload.get("sub")
            if not user_id_raw:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token payload缺少用户ID",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            try:
                user_id = int(str(user_id_raw))
                if user_id <= 0:
                    raise ValueError("Invalid user_id")
            except (ValueError, TypeError) as e:
                logger.warning(f"[Security] 无效的user_id格式: {user_id_raw}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token payload格式错误",
                    headers={"WWW-Authenticate": "Bearer"},
                )
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
            logger.error(f"[Error] 获取当前用户失败: {e}")
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
            async with await self.db.session() as session:
                stmt = select(self.component.user_orm_model).offset(skip).limit(limit)
                result = await session.execute(stmt)
                users = result.scalars().all()

                user_infos = []
                for db_user in users:
                    user_info = await self._build_user_info(session, db_user)
                    user_infos.append(user_info)

                return user_infos
        except Exception as e:
            logger.error(f"[Error] 获取用户列表失败: {e}")
            return []

    async def update_user_info(self, user_id: str, user_info: UserInfo) -> UserInfo:
        """
        完整更新用户信息（包括基本信息和角色）

        Args:
            user_id: 用户UUID
            user_info: 完整的用户信息（包含用户、角色）

        Returns:
            更新后的完整用户信息

        Raises:
            HTTPException: 用户不存在或更新失败
        """
        try:
            async with await self.db.session() as session:
                # 检查用户是否存在
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.user_id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"用户ID {user_id} 不存在"
                    )

                # 更新用户基本信息
                if user_info.user:
                    await self._update_user_basic_info(session, db_user, user_info.user)

                # 更新用户角色
                if user_info.roles is not None:
                    await self._update_user_roles(session, user_id, user_info.roles)

                # 提交事务
                await session.commit()
                await session.refresh(db_user)

                logger.info(f"[Success] 用户信息完整更新成功: user_id={user_id}")

                return await self._build_user_info(session, db_user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] 更新用户信息失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新失败: {str(e)}"
            )

    async def update_user_field(self, user_id: str, field_name: str, field_value: Any) -> UserInfo:
        """
        更新用户的单个字段

        Args:
            user_id: 用户UUID
            field_name: 要更新的字段名
            field_value: 新的字段值

        Returns:
            更新后的完整用户信息

        Raises:
            HTTPException: 用户不存在或字段不存在
        """
        try:
            async with await self.db.session() as session:
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.user_id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"用户ID {user_id} 不存在"
                    )

                if not hasattr(db_user, field_name):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"字段 '{field_name}' 不存在"
                    )

                # 特殊处理密码字段
                if field_name == 'password':
                    field_value = self.password_encoder.encode(field_value)

                setattr(db_user, field_name, field_value)
                await session.commit()
                await session.refresh(db_user)

                logger.info(f"[Success] 用户字段更新成功: user_id={user_id}, field={field_name}")

                return await self._build_user_info(session, db_user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] 更新用户字段失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新字段失败: {str(e)}"
            )

    async def update_user_roles(self, user_id: str, roles: List[Role]) -> UserInfo:
        """
        更新用户的角色（替换所有角色）

        Args:
            user_id: 用户UUID
            roles: 新的角色列表

        Returns:
            更新后的完整用户信息

        Raises:
            HTTPException: 用户不存在或更新失败
        """
        try:
            async with await self.db.session() as session:
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.user_id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"用户ID {user_id} 不存在"
                    )

                await self._update_user_roles(session, db_user.user_id, roles)  # 使用 UUID
                await session.commit()

                logger.info(f"[Success] 用户角色更新成功: user_id={user_id}")

                return await self._build_user_info(session, db_user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] 更新用户角色失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新角色失败: {str(e)}"
            )

    async def delete_user(self, user_id: str) -> bool:
        """
        删除用户（软删除）

        Args:
            user_id: 用户UUID

        Returns:
            是否删除成功

        Raises:
            HTTPException: 用户不存在
        """
        try:
            async with await self.db.session() as session:
                stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.user_id == user_id)
                result = await session.execute(stmt)
                db_user = result.scalar_one_or_none()

                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"用户ID {user_id} 不存在"
                    )

                # 删除用户角色关联
                stmt = delete(self.component.user_role_orm_model).where(
                    self.component.user_role_orm_model.user_id == user_id
                )
                await session.execute(stmt)

                # 删除用户
                await session.delete(db_user)
                await session.commit()

                logger.info(f"[Success] 用户删除成功: user_id={user_id}")
                return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] 删除用户失败: {e}")
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
            db_user: 用户数据库对象
            
        Returns:
            完整的用户信息
        """
        # 构造用户基本信息（不返回密码）
        user = User(
            id=db_user.id,
            user_id=db_user.user_id,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            email=db_user.email,
            active=db_user.active,
        )

        # 查询用户角色
        stmt = select(self.component.role_orm_model).join(
            self.component.user_role_orm_model,
            self.component.user_role_orm_model.role_code == self.component.role_orm_model.code
        ).where(self.component.user_role_orm_model.user_id == db_user.user_id)
        result = await session.execute(stmt)
        roles = [Role.model_validate(role) for role in result.scalars().all()]

        # 查询用户权限（通过角色）
        permissions = []
        if roles:
            role_codes = [role.code for role in roles]
            stmt = select(self.component.permission_orm_model).join(
                self.component.role_permission_orm_model,
                self.component.role_permission_orm_model.permission_code == self.component.permission_orm_model.code
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

        # 检查邮箱唯一性
        if 'email' in update_fields and update_fields['email'] != db_user.email:
            stmt = select(self.component.user_orm_model).where(
                self.component.user_orm_model.email == update_fields['email']
            )
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"邮箱 {update_fields['email']} 已被使用"
                )

        # 特殊处理密码
        if 'password' in update_fields and update_fields['password']:
            update_fields['password'] = self.password_encoder.encode(update_fields['password'])

        # 更新字段
        for field, value in update_fields.items():
            setattr(db_user, field, value)

        # 更新时间戳
        db_user.modifier = "system"
        db_user.modified_time = datetime.now(UTC)

    async def _update_user_roles(self, session: AsyncSession, user_id: str, roles: List[Role]) -> None:
        """
        更新用户角色（替换所有角色）
        
        Args:
            session: 数据库会话
            user_id: 用户UUID
            roles: 新的角色列表
        """
        # 删除现有角色关联
        stmt = delete(self.component.user_role_orm_model).where(
            self.component.user_role_orm_model.user_id == user_id  # UUID 字符串
        )
        await session.execute(stmt)

        # 添加新角色
        for role in roles:
            stmt = select(self.component.role_orm_model).where(self.component.role_orm_model.code == role.code)
            result = await session.execute(stmt)
            db_role = result.scalar_one_or_none()

            if not db_role:
                logger.warning(f"[Warning] 角色不存在 {role.code}，跳过分配")
                continue

            # 创建关联
            user_role = self.component.user_role_orm_model(
                user_id=user_id,  # UUID 字符串
                role_code=db_role.code  # 角色代码
            )
            session.add(user_role)
