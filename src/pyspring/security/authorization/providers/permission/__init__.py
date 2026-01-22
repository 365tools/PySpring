"""
权限服务提供者
"""
from pyspring.security.authorization.providers.permission.cached import CachedPermissionService
from pyspring.security.authorization.providers.permission.default import DefaultPermissionService

__all__ = ['DefaultPermissionService', 'CachedPermissionService']
