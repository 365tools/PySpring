"""
默认权限服务实现

负责用户权限判定，支持：
- 角色级权限检查
- 细粒度权限检查（支持通配符）
- 权限继承和层级
"""
from typing import Any

from pyspring.core.log.instance import logger
from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.role import IRoleProvider


class DefaultPermissionService(IPermissionService):
    """
    默认权限判定服务
    
    通过IRoleProvider查询用户角色和权限，然后进行权限匹配
    支持通配符权限匹配（如 'user:*' 匹配 'user:read'）
    """

    def __init__(self, role_provider: IRoleProvider):
        """
        初始化权限服务
        
        Args:
            role_provider: 角色提供者，用于查询用户角色和权限
        """
        self.role_provider = role_provider
        logger.debug("[DefaultPermissionService] 权限服务已初始化")

    async def has_permission(self, user_id: Any, permission: str) -> bool:
        """
        检查用户是否拥有特定权限（细粒度权限检查）
        
        实现逻辑：
        1. 获取用户的所有有效角色（包含继承）
        2. 获取这些角色的所有权限
        3. 检查权限是否匹配（支持通配符 '*'）
        
        Args:
            user_id: 用户 ID
            permission: 权限字符串（如 'user:read', 'article:*'）
            
        Returns:
            bool: 是否拥有权限
        """
        # 1. 获取用户的有效角色（包含继承）
        user_roles = await self.role_provider.get_effective_roles(user_id)
        if not user_roles:
            logger.debug(f"[Permission] 用户 {user_id} 没有任何角色")
            return False

        # 2. 获取所有角色的权限
        all_permissions = set()
        for role in user_roles:
            role_permissions = await self.role_provider.get_role_permissions(role)
            all_permissions.update(role_permissions)

        if not all_permissions:
            logger.debug(f"[Permission] 用户 {user_id} 的角色没有任何权限")
            return False

        # 3. 检查权限匹配（支持通配符）
        # 精确匹配
        if permission in all_permissions:
            logger.debug(f"[Permission] 用户 {user_id} 拥有权限 {permission} (精确匹配)")
            return True

        # 通配符匹配（如 'user:*' 匹配 'user:read', 'user:write'）
        for perm in all_permissions:
            if self._permission_matches(permission, perm):
                logger.debug(f"[Permission] 用户 {user_id} 拥有权限 {permission} (通配符匹配: {perm})")
                return True

        logger.debug(f"[Permission] 用户 {user_id} 没有权限 {permission}")
        return False

    def _permission_matches(self, required: str, granted: str) -> bool:
        """
        检查权限是否匹配（支持通配符）
        
        匹配规则：
        - 精确匹配: 'user:read' matches 'user:read'
        - 通配符匹配: 'user:read' matches 'user:*'
        - 全局通配符: 'user:read' matches '*'
        - 部分通配符: 'user:article:read' matches 'user:*:read'
        
        Args:
            required: 需要的权限
            granted: 已授予的权限
            
        Returns:
            bool: 是否匹配
        """
        # 全局通配符
        if granted == '*':
            return True

        # 精确匹配
        if granted == required:
            return True

        # 前缀通配符（如 'user:*'，但不包括中间有通配符的如'user:*:read'）
        if granted.endswith(':*') and granted.count('*') == 1:
            prefix = granted[:-2]  # 移除 ':*'
            return required.startswith(prefix + ':') or required == prefix

        # 逐部分匹配（如 'user:*:read' or 'admin:*:*'）
        if '*' in granted:
            granted_parts = granted.split(':')
            required_parts = required.split(':')

            if len(granted_parts) != len(required_parts):
                return False

            for g_part, r_part in zip(granted_parts, required_parts):
                if g_part == '*':
                    continue
                if g_part != r_part:
                    return False

            return True

        return False

    async def has_role(self, user_id: Any, role: str) -> bool:
        """
        检查用户是否拥有特定角色（支持角色继承）
        
        Args:
            user_id: 用户 ID
            role: 角色代码
            
        Returns:
            bool: 是否拥有角色（包含继承）
        """
        # 使用有效角色（包含继承）
        roles = await self.role_provider.get_effective_roles(user_id)
        has = role in roles

        if has:
            logger.debug(f"[Permission] 用户 {user_id} 拥有角色 {role}")
        else:
            logger.debug(f"[Permission] 用户 {user_id} 没有角色 {role}")

        return has
