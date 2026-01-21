from typing import List, Any

from sqlalchemy import select

from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.config.entity.config import SecurityEntityConfiguration
from pyspring.security.authorization.contracts.role import IRoleProvider


class DefaultRoleProvider(IRoleProvider):
    """
    默认的角色提供者（基于数据库）
    允许用户通过实现 IRoleProvider 接口并注册 Bean 来替换此默认实现
    """

    def __init__(self, db_manager: DBManagerService, component: SecurityEntityConfiguration):
        self.db_manager = db_manager
        self.component = component

    async def get_user_roles(self, user_id: Any) -> List[str]:
        """从数据库查询用户的角色代码列表"""
        session = await self.db_manager.session()

        # 获取表模型
        RoleTable = self.component.role_orm_model
        UserTable = self.component.user_orm_model
        UserRoleTable = self.component.user_role_orm_model

        async with session:
            # Join UserRole -> Role -> User
            # 注意: BaseUserRoleTable 使用 id 关联 (user_id, role_id are INTs -> User.id, Role.id)
            stmt = (
                select(RoleTable.code)
                .join(UserRoleTable, RoleTable.id == UserRoleTable.role_id)
                .join(UserTable, UserTable.id == UserRoleTable.user_id)
                .where(UserTable.user_id == str(user_id))  # Assume business ID
            )

            result = await session.execute(stmt)
            roles = result.scalars().all()
            return list(roles)

    async def get_role_permissions(self, role_name: str) -> List[str]:
        """获取指定角色的权限代码列表"""
        session = await self.db_manager.session()

        # 获取表模型
        RoleTable = self.component.role_orm_model
        PermissionTable = self.component.permission_orm_model
        RolePermissionTable = self.component.role_permission_orm_model

        async with session:
            # Join RolePermission -> Permission -> Role
            # 注意: BaseRolePermissionTable 使用 code 关联 (role_code, permission_code are Strings)
            stmt = (
                select(PermissionTable.code)
                .join(RolePermissionTable, PermissionTable.code == RolePermissionTable.permission_code)
                .join(RoleTable, RoleTable.code == RolePermissionTable.role_code)
                .where(RoleTable.code == role_name)
            )

            result = await session.execute(stmt)
            permissions = result.scalars().all()
            return list(permissions)
