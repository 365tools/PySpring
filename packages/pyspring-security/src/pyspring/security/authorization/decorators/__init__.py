"""
Authorization装饰器模块
"""
from pyspring.security.authorization.decorators.require import (
    require_all_permissions,
    require_any_permission,
    require_permission,
    require_role,
)

__all__ = [
    'require_permission',
    'require_role',
    'require_any_permission',
    'require_all_permissions'
]
