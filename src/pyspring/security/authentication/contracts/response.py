from abc import ABC, abstractmethod
from typing import Any

from pyspring.ioc.interfaces.core import IManaged


class IResponseBuilder(IManaged, ABC):
    """
    响应构建器接口
    负责构造 API 响应
    """

    @abstractmethod
    def build_login_response(self, user: Any, access_token: str, refresh_token: str, **kwargs) -> Any:
        """构造登录成功响应"""
        pass

    @abstractmethod
    def build_logout_response(self, **kwargs) -> Any:
        """构造登出响应"""
        pass

    @abstractmethod
    def build_token_response(self, access_token: str, **kwargs) -> Any:
        """构造刷新 Token 响应"""
        pass
