"""
权限服务提供者
"""
from pyspring.security.authorization.providers.permission.default import DefaultPermissionService
from pyspring.security.authorization.providers.permission.cached import CachedPermissionService
from pyspring.security.authorization.providers.permission.advanced import AdvancedPermissionService

__all__ = ['DefaultPermissionService', 'CachedPermissionService', 'AdvancedPermissionService']
