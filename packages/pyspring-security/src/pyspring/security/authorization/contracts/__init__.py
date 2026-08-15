"""
授权契约接口

定义授权模块的核心接口：
- IPermissionService: 权限服务接口
- IRoleProvider: 角色提供者接口
- IPathPermissionProvider: 路径规则提供者接口
"""
from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.role import IRoleProvider
from pyspring.security.authorization.contracts.rule import IPathPermissionProvider

__all__ = [
    'IPermissionService',
    'IRoleProvider',
    'IPathPermissionProvider',
]
