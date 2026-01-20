from abc import ABC, abstractmethod
from typing import Any, Optional

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


class IUserProvider(ISingletonService, ABC):
    """
    用户提供者接口
    负责从数据源（数据库、LDAP、API等）查找用户
    """

    @abstractmethod
    async def get_user_by_id(self, user_id: Any) -> Optional[Any]:
        """根据 ID 获取用户"""
        pass

    @abstractmethod
    async def get_user_by_identity(self, identity: str) -> Optional[Any]:
        """根据标识（用户名/邮箱/手机号）获取用户"""
        pass


class IUserManagerService(ISingletonService, ABC):
    """
    用户管理服务接口
    负责用户信息的查询、更新等
    """

    @abstractmethod
    async def get_user_by_id(self, user_id: Any) -> Optional[Any]:
        """根据ID获取用户"""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Any]:
        """根据邮箱获取用户"""
        pass

    @abstractmethod
    async def get_current_user(self, token: Optional[str] = None) -> Optional[Any]:
        """获取当前用户"""
        pass

    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 100) -> Any:
        """获取用户列表"""
        pass

    @abstractmethod
    async def update_user_info(self, user_id: Any, user_info: Any) -> Any:
        """完整更新用户信息"""
        pass

    @abstractmethod
    async def update_user_field(self, user_id: Any, field_name: str, field_value: Any) -> Any:
        """更新单个字段"""
        pass
