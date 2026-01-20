from abc import ABC, abstractmethod
from typing import List, Any

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


class IRoleProvider(ISingletonService, ABC):
    """
    角色提供者接口
    负责获取用户的角色信息
    """

    @abstractmethod
    async def get_user_roles(self, user_id: Any) -> List[str]:
        """获取指定用户的角色列表"""
        pass

    @abstractmethod
    async def get_role_permissions(self, role_name: str) -> List[str]:
        """获取指定角色的权限列表"""
        pass
