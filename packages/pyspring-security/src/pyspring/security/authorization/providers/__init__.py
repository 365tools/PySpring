"""
授权提供者

包含角色、权限、规则等提供者实现
"""
from pyspring.security.authorization.providers.permission.default import DefaultPermissionService
from pyspring.security.authorization.providers.role.database import DefaultRoleProvider
from pyspring.security.authorization.providers.rule.config import DefaultPathPermissionProvider

__all__ = [
    'DefaultPermissionService',
    'DefaultRoleProvider',
    'DefaultPathPermissionProvider',
]
