from abc import ABC, abstractmethod
from typing import Any

from pyspring.ioc.interfaces.core import IManaged


class ILoginService(IManaged, ABC):
    """
    登录服务接口
    负责登录流程编排
    """

    @abstractmethod
    async def login(self, request: Any) -> Any:
        """处理登录"""
        pass

    @abstractmethod
    async def logout(self, token: str) -> Any:
        """处理登出"""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Any:
        """刷新 Token"""
        pass


class IRegisterService(IManaged, ABC):
    """
    注册服务接口
    负责用户注册流程
    """

    @abstractmethod
    async def register(self, request: Any) -> Any:
        """注册新用户"""
        pass
