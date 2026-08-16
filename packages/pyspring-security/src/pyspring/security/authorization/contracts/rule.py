from abc import ABC, abstractmethod

from pyspring.core.ioc.interfaces.core import IManaged


class IPathPermissionProvider(IManaged, ABC):
    """
    路径权限规则提供者接口
    负责加载 URL 路径与其所需权限/角色的映射规则
    """

    @abstractmethod
    def get_path_rules(self) -> dict[str, list[str]]:
        """
        获取路径规则
        
        Returns:
            dict[str, list[str]]: 路径 -> 所需角色/权限列表 的映射
            例如: {"/api/admin/": ["admin"], "/api/user/": ["user", "admin"]}
        """
        pass
