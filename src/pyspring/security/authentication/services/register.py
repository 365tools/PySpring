from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pyspring.ioc.annotations import ConditionalOnMissingBean
from pyspring.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.authentication.contracts.flow import IRegisterService
from pyspring.security.authentication.contracts.password import IPasswordEncoder
from pyspring.security.authentication.contracts.response import UserInfo, User, Role, Permission


@ConditionalOnMissingBean(IRegisterService)
class DefaultRegisterService(IRegisterService):
    """
    默认用户注册服务
    
    负责用户注册、角色分配等功能
    """

    def __init__(self, db: DBManagerService, component: SecurityEntityConfiguration, password_encoder: IPasswordEncoder):
        """
        初始化注册服务
        
        Args:
            db: 数据库管理服务
            component: 安全组件配置
            password_encoder: 密码编码器
        """
        self.db = db
        self.component = component
        self.password_encoder = password_encoder

    async def register(self, request: UserInfo) -> UserInfo:
        """
        注册新用户
        
        安全说明：
        - 角色不能由用户自己指定，防止权限提升攻击
        - 新注册用户默认分配 'guest' 角色
        - 管理员角色需要通过后台审批授予
        
        Args:
            request: 用户注册信息(仅包含用户基本信息，不含角色)

        Returns:
            创建的完整用户信息

        Raises:
            HTTPException: 用户已存在或其他错误
        """
        try:
            async with await self.db.session() as session:
                # 1. 检查用户是否已存在
                await self._check_user_exists(session, request.user)

                # 2. 创建用户
                db_user = await self._create_user(session, request.user)

                # 3. 分配默认角色（固定为'user'角色，不接受外部输入）
                await self._assign_default_role(session, db_user)

                # 4. 提交事务
                await session.commit()
                await session.refresh(db_user)

                logger.info(f"[Success] 用户注册成功: {db_user.email} (UUID: {db_user.user_id})，已分配默认角色: guest")

                # 5. 构造返回结果
                return await self._build_user_info(session, db_user)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] 用户注册失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"注册失败: {str(e)}"
            )

    async def _check_user_exists(self, session: AsyncSession, user: User) -> None:
        """
        检查用户是否已存在
        
        Args:
            session: 数据库会话
            user: 用户信息
            
        Raises:
            HTTPException: 用户已存在
        """
        # 检查邮箱是否已被注册
        stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.email == user.email)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="注册失败：用户信息已存在"  # 统一错误消息，不泄露具体字段
            )

        # 检查 user_id 是否已被使用
        stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.user_id == user.user_id)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="注册失败：用户信息已存在"  # 统一错误消息
            )

    async def _create_user(self, session: AsyncSession, user: User) -> Any:
        """
        创建用户
        
        Args:
            session: 数据库会话
            user: 用户信息
            
        Returns:
            创建的用户数据库对象
        """
        if not user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码不能为空"
            )

        hashed_password = self.password_encoder.encode(user.password)

        # 创建用户数据库对象
        db_user = self.component.user_orm_model(
            user_id=user.user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password=hashed_password,
        )

        session.add(db_user)
        await session.flush()  # 刷新以获取自增ID

        return db_user

    async def _assign_default_role(self, session: AsyncSession, user: Any) -> None:
        """
        为新用户分配默认角色
        
        安全说明：
        - 固定分配 'guest' 角色，不接受外部参数
        - 管理员等高级角色必须通过管理后台授予
        
        Args:
            session: 数据库会话
            user: 用户对象（使用 user.user_id UUID）
        """
        default_role_code = "guest"  # 默认角色固定为 'guest'

        # 检查默认角色是否存在
        stmt = select(self.component.role_orm_model).where(
            self.component.role_orm_model.code == default_role_code
        )
        result = await session.execute(stmt)
        db_role = result.scalar_one_or_none()

        if not db_role:
            logger.warning(
                f"[Warning] 默认角色'{default_role_code}'不存在，用户注册成功但未分配角色。"
                "请在数据库中创建'guest'角色。"
            )
            return

        # 创建用户角色关联
        user_role = self.component.user_role_orm_model(
            user_id=user.user_id,  # UUID
            role_code=default_role_code
        )
        session.add(user_role)
        logger.info(f"[Success] 为新用户分配默认角色: {default_role_code}")
    
    async def _assign_roles(self, session: AsyncSession, user: Any, roles: list[Role]) -> None:
        """
        为用户分配角色（仅供管理员使用）
        
        ⚠️ 警告：此方法仅应由管理员接口调用，不应在用户注册时使用
        
        Args:
            session: 数据库会话
            user: 用户对象（使用 user.user_id UUID）
            roles: 角色列表
        """
        for role in roles:
            # 检查角色是否存在
            stmt = select(self.component.role_orm_model).where(self.component.role_orm_model.code == role.code)
            result = await session.execute(stmt)
            db_role = result.scalar_one_or_none()

            if not db_role:
                logger.warning(f"[Warning] 角色不存在: {role.code}, 跳过分配")
                continue

            # 检查是否已分配
            stmt = select(self.component.user_role_orm_model).where(
                self.component.user_role_orm_model.user_id == user.user_id,
                self.component.user_role_orm_model.role_code == role.code
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                logger.info(f"用户已拥有角色: {role.code}")
                continue

            # 创建用户角色关联
            user_role = self.component.user_role_orm_model(
                user_id=user.user_id,  # UUID
                role_code=role.code  # 角色代码
            )
            session.add(user_role)
            logger.info(f"[Success] 为用户分配角色: {role.code}")

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
        )

        # 查询用户角色
        stmt = select(self.component.role_orm_model).join(
            self.component.user_role_orm_model, self.component.user_role_orm_model.role_code == self.component.role_orm_model.code
        ).where(self.component.user_role_orm_model.user_id == db_user.user_id)
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
