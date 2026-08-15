"""
默认角色提供者（基于数据库）

负责从数据库查询：
- 用户的角色列表
- 角色的权限列表
- 角色继承层次
"""
from typing import Any

from pyspring.core.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.authorization.contracts.role import IRoleProvider
from sqlalchemy import select


class DefaultRoleProvider(IRoleProvider):
    """
    默认的角色提供者（基于数据库）
    
    通过ORM查询用户角色和角色权限，支持角色继承
    用户可以通过实现IRoleProvider接口并注册@Bean来替换此实现
    """

    def __init__(self, db_manager: DBManagerService, component: SecurityEntityConfiguration):
        """
        初始化角色提供者
        
        Args:
            db_manager: 数据库管理服务
            component: 安全实体配置，提供ORM模型
        """
        self.db_manager = db_manager
        self.component = component
        # 默认角色继承层次（可通过数据库配置覆盖）
        self._default_hierarchy = {
            'admin': ['manager', 'user'],
            'manager': ['user']
        }
        logger.debug("[DefaultRoleProvider] 角色提供者已初始化")

    async def get_user_roles(self, user_id: Any) -> list[str]:
        """
        从数据库查询用户的角色代码列表
        
        查询逻辑（新）：
        UserRole -> Role
        通过 user_id (UUID) 直接关联，使用业务代码关联
        
        Args:
            user_id: 用户UUID（user_id字段）
            
        Returns:
            list[str]: 角色代码列表（如 ['admin', 'user']）
        """
        session = await self.db_manager.session()

        # 获取表模型
        RoleTable = self.component.role_orm_model
        UserRoleTable = self.component.user_role_orm_model

        try:
            async with session:
                # 简化查询：UserRole -> Role
                # UserRoleTable.user_id = user_id (UUID)
                # UserRoleTable.role_code = RoleTable.code
                stmt = (
                    select(RoleTable.code)
                    .join(UserRoleTable, RoleTable.code == UserRoleTable.role_code)
                    .where(UserRoleTable.user_id == str(user_id))  # UUID 字符串
                )

                result = await session.execute(stmt)
                roles = result.scalars().all()
                role_list = list(roles)

                logger.debug(f"[RoleProvider] 用户 {user_id} 的角色: {role_list}")
                return role_list
        except Exception as e:
            logger.error(f"[RoleProvider] 查询用户角色失败: {e}")
            return []

    async def get_role_permissions(self, role_name: str) -> list[str]:
        """
        获取指定角色的权限代码列表
        
        查询逻辑：
        Role -> RolePermission -> Permission
        
        Args:
            role_name: 角色代码（如 'admin'）
            
        Returns:
            list[str]: 权限代码列表（如 ['user:read', 'user:write']）
        """
        session = await self.db_manager.session()

        # 获取表模型
        RoleTable = self.component.role_orm_model
        PermissionTable = self.component.permission_orm_model
        RolePermissionTable = self.component.role_permission_orm_model

        try:
            async with session:
                # Join查询: RolePermission -> Permission -> Role
                # RolePermissionTable使用code关联（不是id）
                stmt = (
                    select(PermissionTable.code)
                    .join(RolePermissionTable, PermissionTable.code == RolePermissionTable.permission_code)
                    .join(RoleTable, RoleTable.code == RolePermissionTable.role_code)
                    .where(RoleTable.code == role_name)
                )

                result = await session.execute(stmt)
                permissions = result.scalars().all()
                perm_list = list(permissions)

                logger.debug(f"[RoleProvider] 角色 {role_name} 的权限: {perm_list}")
                return perm_list
        except Exception as e:
            logger.error(f"[RoleProvider] 查询角色权限失败: {e}")
            return []

    async def get_role_hierarchy(self) -> dict[str, list[str]]:
        """
        获取角色继承层次结构
        
        默认实现：
        - admin继承manager和user
        - manager继承user
        
        扩展方式：
        1. 子类覆盖此方法，从数据库读取配置
        2. 从配置文件读取（如YAML）
        
        Returns:
            dict[str, list[str]]: 角色继承映射
        """
        return self._default_hierarchy.copy()
