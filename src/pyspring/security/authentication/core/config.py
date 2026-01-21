from typing import List

from pyspring.ioc.annotations.decorators import Configuration, Bean, ConditionalOnMissingBean

from pyspring.core.services.system import SystemService
# 导入其他依赖
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.contracts.interface.flow import ILoginService
from pyspring.security.authentication.contracts.interface.flow import IRegisterService
from pyspring.security.authentication.contracts.interface.login import ILoginProvider
from pyspring.security.authentication.contracts.interface.response import IResponseBuilder
from pyspring.security.authentication.contracts.interface.token import ITokenPayloadBuilder
from pyspring.security.authentication.contracts.interface.token import ITokenService
from pyspring.security.authentication.core.factory import AuthProviderFactory
from pyspring.security.authentication.implementations.request.base import BaseAuthenticationProvider
from pyspring.security.authentication.implementations.response.builder.default import DefaultResponseBuilder
from pyspring.security.authentication.implementations.token.builder.default import DefaultTokenPayloadBuilder
# 导入接口和默认实现
from .component import SecurityEntityConfiguration
from .manager import DefaultLoginProviderManager
from ..contracts.interface.user import IUserProvider, IUserManagerService
from ..implementations.login.password import DefaultPasswordLoginProvider
from ..implementations.user.database import DefaultUserProvider
from ..services.context_validator import SecurityContextManagerService
from ..services.flow.login import DefaultLoginService
from ..services.flow.manager import DefaultUserManagerService
from ..services.flow.register import DefaultRegisterService
from ..services.flow.token import DefaultTokenManagerService


@Configuration
class AuthenticationConfiguration:
    """
    PySpring 安全模块(认证部分)的默认自动配置。
    负责注册所有默认的策略实现（Provider, Builder 等）。
    """

    @Bean
    @ConditionalOnMissingBean(SecurityEntityConfiguration)
    def default_security_entity_configuration(self) -> SecurityEntityConfiguration:
        """Provide a default SecurityEntityConfiguration Bean if the user hasn't defined one."""
        return SecurityEntityConfiguration()

    @Bean
    @ConditionalOnMissingBean(IUserProvider)
    def default_user_provider(self, db: DBManagerService, default_security_entity_configuration: SecurityEntityConfiguration) -> IUserProvider:
        """Create default instance if user defined IUserProvider Bean is missing."""
        return DefaultUserProvider(db, default_security_entity_configuration)

    @Bean
    @ConditionalOnMissingBean(DefaultPasswordLoginProvider)
    def default_password_login_provider(self, default_user_provider: IUserProvider, db: DBManagerService) -> DefaultPasswordLoginProvider:
        """Create default DefaultPasswordLoginProvider."""
        return DefaultPasswordLoginProvider(default_user_provider, db)

    @Bean
    @ConditionalOnMissingBean(ILoginProvider)
    def default_login_provider(self, default_password_login_provider: DefaultPasswordLoginProvider) -> ILoginProvider:
        """
        Create the main DefaultLoginProviderManager (which is also an ILoginProvider).
        It manages a list of providers. By default, only password_provider is added.
        """
        return DefaultLoginProviderManager([default_password_login_provider])

    @Bean
    @ConditionalOnMissingBean(IResponseBuilder)
    def default_response_builder(self, default_security_entity_configuration: SecurityEntityConfiguration, system_service: SystemService) -> IResponseBuilder:
        """Create default instance if user defined IResponseBuilder Bean is missing."""
        return DefaultResponseBuilder(default_security_entity_configuration, system_service)

    @Bean
    @ConditionalOnMissingBean(ITokenPayloadBuilder)
    def default_token_payload_builder(self, db: DBManagerService, default_security_entity_configuration: SecurityEntityConfiguration) -> ITokenPayloadBuilder:
        """只有当用户没有定义自己的 ITokenPayloadBuilder Bean 时，才创建这个默认实例。"""
        return DefaultTokenPayloadBuilder(db, default_security_entity_configuration)

    @Bean
    @ConditionalOnMissingBean(ITokenService)
    def default_token_service(self, system_service: SystemService) -> ITokenService:
        """只有当用户没有定义自己的 ITokenService Bean 时，才创建这个默认实例。"""
        # 移除 cache/db 注入，改为内部懒加载
        return DefaultTokenManagerService(system_service)

    @Bean
    @ConditionalOnMissingBean(ILoginService)
    def default_login_service(
            self,
            default_user_provider: IUserProvider,
            default_login_provider: ILoginProvider,
            default_response_builder: IResponseBuilder,
            default_token_payload_builder: ITokenPayloadBuilder,
            security_context_manager_service: SecurityContextManagerService
    ) -> ILoginService:
        """只有当用户没有定义自己的 ILoginService Bean 时，才创建这个默认实例。"""
        # 移除 default_token_service
        return DefaultLoginService(
            default_user_provider,
            default_login_provider,
            default_response_builder,
            default_token_payload_builder,
            security_context_manager_service
        )

    @Bean
    @ConditionalOnMissingBean(IRegisterService)
    def default_register_service(self, db: DBManagerService, default_security_entity_configuration: SecurityEntityConfiguration) -> IRegisterService:
        """只有当用户没有定义自己的 IRegisterService Bean 时，才创建这个默认实例。"""
        return DefaultRegisterService(db, default_security_entity_configuration)

    @Bean
    @ConditionalOnMissingBean(IUserManagerService)
    def default_user_manager_service(self, db: DBManagerService, default_security_entity_configuration: SecurityEntityConfiguration) -> IUserManagerService:
        """只有当用户没有定义自己的 IUserManagerService Bean 时，才创建这个默认实例。"""
        # 移除 token_service 注入，改为内部懒加载
        return DefaultUserManagerService(db, default_security_entity_configuration)

    @Bean
    def authentication_providers(self) -> List[BaseAuthenticationProvider]:
        """Create authentication providers from config."""
        # 移除 default_token_service 依赖，在 Factory 内部懒加载
        return AuthProviderFactory.create_providers_from_config(token_manager=None)
