from abc import ABC, abstractmethod
from typing import Any

from pyspring.core.ioc.interfaces.core import IManaged


class IRoleProvider(IManaged, ABC):
    """
    角色提供者接口
    负责获取用户的角色信息，支持角色继承
    """

    @abstractmethod
    async def get_user_roles(self, user_id: Any) -> list[str]:
        """
        获取指定用户的角色列表

        Args:
            user_id: 用户ID

        Returns:
            list[str]: 角色代码列表
        """
        pass

    @abstractmethod
    async def get_role_permissions(self, role_name: str) -> list[str]:
        """
        获取指定角色的权限列表

        Args:
            role_name: 角色代码

        Returns:
            list[str]: 权限代码列表
        """
        pass

    @abstractmethod
    async def get_role_hierarchy(self) -> dict[str, list[str]]:
        """
        获取角色继承层次结构

        返回角色继承映射，key为角色，value为其继承的角色列表
        例如：{'admin': ['manager', 'user'], 'manager': ['user']}
        表示admin继承manager和user，manager继承user

        Returns:
            dict[str, list[str]]: 角色继承映射
        """
        pass

    async def get_effective_roles(self, user_id: Any) -> list[str]:
        """
        获取用户的有效角色（包含继承的角色）

        默认实现：基于角色继承层次自动计算

        Args:
            user_id: 用户ID

        Returns:
            list[str]: 包含继承关系的角色列表
        """
        # 1. 获取用户的直接角色
        direct_roles = await self.get_user_roles(user_id)

        # 2. 获取角色继承关系
        hierarchy = await self.get_role_hierarchy()

        # 3. 递归展开继承
        effective_roles = set(direct_roles)

        def expand_roles(role: str):
            """递归展开角色继承"""
            if role in hierarchy:
                for inherited in hierarchy[role]:
                    if inherited not in effective_roles:
                        effective_roles.add(inherited)
                        expand_roles(inherited)

        for role in direct_roles:
            expand_roles(role)

        return list(effective_roles)
