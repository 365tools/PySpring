from typing import Any

from pyspring.core.ioc.annotations import ConditionalOnMissingBean
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.authentication.contracts.response import IResponseBuilder
from pyspring.security.authentication.contracts.token import ITokenService


@ConditionalOnMissingBean(IResponseBuilder)
class DefaultResponseBuilder(IResponseBuilder):
    """
    默认响应构建器（策略无关）

    职责：构建登录、登出响应
    设计：从TokenService动态获取token类型和过期时间，支持多种token策略
    """

    def __init__(self, component: SecurityEntityConfiguration, token_service: ITokenService):
        self.component = component
        self.token_service = token_service

    def build_login_response(self, user: Any, access_token: str, refresh_token: str, **kwargs) -> Any:
        warning_msg = kwargs.get("warning_msg", "")
        generator = self.token_service.token_generator

        return self.component.login_response_schema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=generator.get_token_type().lower(),
            expires_in=generator.get_access_token_expire(),
            refresh_token_expire=generator.get_refresh_token_expire(),
            message=warning_msg if warning_msg else "登录成功",
        )

    def build_logout_response(self, **kwargs) -> Any:
        return self.component.logout_response_schema(message="登出成功", detail="Token已失效")

    def build_token_response(self, access_token: str, **kwargs) -> Any:
        generator = self.token_service.token_generator

        return self.component.token_response_schema(
            access_token=access_token,
            token_type=generator.get_token_type().lower(),
            expires_in=generator.get_access_token_expire(),
        )
