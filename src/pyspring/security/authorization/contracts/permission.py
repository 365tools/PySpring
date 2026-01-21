from abc import ABC, abstractmethod
from typing import Any

from pyspring.ioc.interfaces import IManaged


class IPermissionService(IManaged, ABC):
    """
    权限服务接口
    负责最终的权限判定
    """

    @abstractmethod
    async def has_permission(self, user_id: Any, permission: str) -> bool:
        """检查用户是否拥有特定权限"""
        pass

    @abstractmethod
    async def has_role(self, user_id: Any, role: str) -> bool:
        """检查用户是否拥有特定角色"""
        pass