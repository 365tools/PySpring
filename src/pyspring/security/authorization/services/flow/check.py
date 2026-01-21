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
        """
        检查用户是否拥有特定权限（细粒度权限检查）
        
        实现逻辑：
        1. 获取用户的所有角色
        2. 获取这些角色的所有权限
        3. 检查权限是否匹配（支持通配符 '*'）
        
        Args:
            user_id: 用户 ID
            permission: 权限字符串（如 'user:read', 'article:*'）
            
        Returns:
            bool: 是否拥有权限
        """
        # 1. 获取用户角色
        user_roles = await self.role_provider.get_user_roles(user_id)
        if not user_roles:
            return False

        # 2. 获取所有角色的权限
        all_permissions = set()
        for role in user_roles:
            role_permissions = await self.role_provider.get_role_permissions(role)
            all_permissions.update(role_permissions)

        # 3. 检查权限匹配（支持通配符）
        # 精确匹配
        if permission in all_permissions:
            return True

        # 通配符匹配（如 'user:*' 匹配 'user:read', 'user:write'）
        for perm in all_permissions:
            if self._permission_matches(permission, perm):
                return True
        
        return False

    def _permission_matches(self, required: str, granted: str) -> bool:
        """
        检查权限是否匹配（支持通配符）
        
        Examples:
            'user:read' matches 'user:read' (精确匹配)
            'user:read' matches 'user:*' (通配符匹配)
            'user:read' matches '*' (全局通配符)
        """
        if granted == '*':
            return True

        granted_parts = granted.split(':')
        required_parts = required.split(':')

        if len(granted_parts) != len(required_parts):
            # 长度不同，检查是否有通配符
            if granted.endswith(':*'):
                prefix = granted[:-2]  # 移除 ':*'
                return required.startswith(prefix + ':')
            return False

        # 逐部分匹配
        for g_part, r_part in zip(granted_parts, required_parts):
            if g_part == '*':
                continue
            if g_part != r_part:
                return False

        return True

    async def has_role(self, user_id: Any, role: str) -> bool:
        """检查用户是否拥有特定角色"""
        roles = await self.role_provider.get_user_roles(user_id)
        return role in roles
