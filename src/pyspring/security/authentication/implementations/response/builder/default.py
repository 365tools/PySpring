from typing import Any

from pyspring.core.services.system import SystemService
from pyspring.security.authentication.contracts.interface.response import IResponseBuilder
from pyspring.security.authentication.core.component import SecurityEntityConfiguration


class DefaultResponseBuilder(IResponseBuilder):
    """
    Default Response Builder
    """

    def __init__(self, component: SecurityEntityConfiguration, system_service: SystemService):
        self.component = component
        self.system = system_service

    def build_login_response(self, user: Any, access_token: str, refresh_token: str, **kwargs) -> Any:
        warning_msg = kwargs.get("warning_msg", "")

        return self.component.login_response_schema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.system.get().authentication.jwt.access_token_expire,
            message=warning_msg if warning_msg else "登录成功"
        )

    def build_logout_response(self, **kwargs) -> Any:
        return self.component.logout_response_schema(
            message="登出成功",
            detail="Token已失效"
        )

    def build_token_response(self, access_token: str, **kwargs) -> Any:
        return self.component.token_response_schema(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.system.get().authentication.jwt.access_token_expire
        )
