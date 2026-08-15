"""
授权Web中间件

提供基于角色的访问控制中间件
"""
from pyspring.security.authorization.web.middleware.role import RoleCheckMiddleware

__all__ = ['RoleCheckMiddleware']
