from typing import Any

from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.role import IRoleProvider


class DefaultPermissionService(IPermissionService):
    """
    默认权限判定服务
    """

    def __init__(self, role_provider: IRoleProvider):
        self.role_provider = role_provider

    async def has_permission(self, user_id: Any, permission: str) -> bool:
        # TODO: Implement granular permission check
        return False

    async def has_role(self, user_id: Any, role: str) -> bool:
        """检查用户是否拥有特定角色"""
        roles = await self.role_provider.get_user_roles(user_id)
        return role in roles
