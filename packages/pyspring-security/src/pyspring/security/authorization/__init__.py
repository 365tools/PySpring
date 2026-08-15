"""
PySpring 授权模块

提供基于角色和权限的访问控制（RBAC）

核心组件：
- config: 授权模块配置（AuthorizationConfiguration）
- contracts: 授权接口定义（IPermissionService, IRoleProvider, IPathPermissionProvider）
- providers: 默认实现（DefaultPermissionService, DefaultRoleProvider, CachedPermissionService等）
- decorators: 权限装饰器（@require_permission, @require_role）
- web: Web中间件（RoleCheckMiddleware）

使用方式：
```python
from pyspring.core.ioc.context import ApplicationContext
from pyspring.security.authorization import require_permission

# 使用装饰器
@require_permission("order:delete")
async def delete_order(order_id: int):
    ...
```
"""
from pyspring.security.authorization.config import AuthorizationConfiguration
from pyspring.security.authorization.contracts import (
    IPermissionService,
    IRoleProvider,
    IPathPermissionProvider
)
from pyspring.security.authorization.decorators import (
    require_permission,
    require_role,
    require_any_permission,
    require_all_permissions
)

__all__ = [
    # 配置
    'AuthorizationConfiguration',

    # 接口
    'IPermissionService',
    'IRoleProvider',
    'IPathPermissionProvider',

    # 装饰器
    'require_permission',
    'require_role',
    'require_any_permission',
    'require_all_permissions',
]
