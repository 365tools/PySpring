"""
Authorization装饰器模块
"""
from pyspring.security.authorization.decorators.require import (
    require_permission,
    require_role,
    require_any_permission,
    require_all_permissions
)

__all__ = [
    'require_permission',
    'require_role',
    'require_any_permission',
    'require_all_permissions'
]
