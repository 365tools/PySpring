"""
认证模块自动配置

使用最新的IOC框架，配置所有默认的认证组件
"""
from typing import List

from pyspring.ioc.annotations.component import Configuration, Bean, ConditionalOnMissingBean
from pyspring.repositories.db.manager import DBManagerService
# 导入配置和工厂
from pyspring.security.authentication.config.entity.config import SecurityEntityConfiguration
# 导入接口
from pyspring.security.authentication.contracts.flow import ILoginService, IRegisterService
from pyspring.security.authentication.contracts.login import ILoginProvider
from pyspring.security.authentication.contracts.request_auth import IRequestAuthenticationProvider
from pyspring.security.authentication.contracts.response import IResponseBuilder
from pyspring.security.authentication.contracts.token import ITokenPayloadBuilder, ITokenService
from pyspring.security.authentication.contracts.user import IUserProvider, IUserManagerService
from pyspring.security.authentication.factories.auth_provider.factory import AuthProviderFactory
from pyspring.security.authentication.factories.login_provider.manager import DefaultLoginProviderManager
# 导入默认实现
from pyspring.security.authentication.providers.login.password import DefaultPasswordLoginProvider
from pyspring.security.authentication.providers.response.builder.default import DefaultResponseBuilder
from pyspring.security.authentication.providers.user.database import DefaultUserProvider
from pyspring.security.authentication.services.context_validator import SecurityContextManagerService
from pyspring.security.authentication.services.login import DefaultLoginService
from pyspring.security.authentication.services.register import DefaultRegisterService
from pyspring.security.authentication.services.user.manager import DefaultUserManagerService
from pyspring.security.authentication.token.builder.default import DefaultTokenPayloadBuilder
from pyspring.security.core.config.loader import SecurityConfigManager


@Configuration
class AuthenticationConfiguration:
    """
    PySpring 安全模块(认证部分)的默认自动配置。
    负责注册所有默认的策略实现（Provider, Builder 等）。
    """

    @Bean()
    def security_config_manager(self) -> SecurityConfigManager:
        """注册SecurityConfigManager为单例Bean"""
        return SecurityConfigManager()

    @Bean()
    @ConditionalOnMissingBean(SecurityEntityConfiguration)
    def default_security_entity_configuration(self) -> SecurityEntityConfiguration:
        """Provide a default SecurityEntityConfiguration Bean if the user hasn't defined one."""
        return SecurityEntityConfiguration()

    @Bean()
    @ConditionalOnMissingBean(IUserProvider)
    def default_user_provider(self, db: DBManagerService, component: SecurityEntityConfiguration) -> IUserProvider:
        """Create default instance if user defined IUserProvider Bean is missing."""
        return DefaultUserProvider(db, component)

    @Bean()
    @ConditionalOnMissingBean(DefaultPasswordLoginProvider)
    def default_password_login_provider(self, default_user_provider: IUserProvider, db: DBManagerService) -> DefaultPasswordLoginProvider:
        """Create default DefaultPasswordLoginProvider."""
        return DefaultPasswordLoginProvider(default_user_provider, db)

    @Bean()
    @ConditionalOnMissingBean(ILoginProvider)
    def default_login_provider(self, default_password_login_provider: DefaultPasswordLoginProvider) -> ILoginProvider:
        """
        Create the main DefaultLoginProviderManager (which is also an ILoginProvider).
        It manages a list of providers. By default, only password_provider is added.
        """
        return DefaultLoginProviderManager([default_password_login_provider])

    @Bean()
    @ConditionalOnMissingBean(IResponseBuilder)
    def default_response_builder(
            self,
            component: SecurityEntityConfiguration,
            token_service: ITokenService
    ) -> IResponseBuilder:
        """创建默认响应构建器（通过IOC注入TokenService）"""
        return DefaultResponseBuilder(component, token_service)

    @Bean()
    @ConditionalOnMissingBean(ITokenPayloadBuilder)
    def default_token_payload_builder(self, db: DBManagerService, component: SecurityEntityConfiguration) -> ITokenPayloadBuilder:
        """只有当用户没有定义自己的 ITokenPayloadBuilder Bean 时，才创建这个默认实例。"""
        return DefaultTokenPayloadBuilder(db, component)

    @Bean()
    @ConditionalOnMissingBean(ITokenService)
    def default_token_service(self) -> ITokenService:
        """只有当用户没有定义自己的 ITokenService Bean 时，才创建这个默认实例。"""
        from pyspring.security.authentication.token.service import TokenService
        return TokenService()

    @Bean()
    @ConditionalOnMissingBean(ILoginService)
    def default_login_service(
            self,
            default_user_provider: IUserProvider,
            default_login_provider: ILoginProvider,
            default_response_builder: IResponseBuilder,
            default_token_payload_builder: ITokenPayloadBuilder,
            security_context_manager_service: SecurityContextManagerService,
            default_token_service: ITokenService
    ) -> ILoginService:
        """只有当用户没有定义自己的 ILoginService Bean 时，才创建这个默认实例。"""
        return DefaultLoginService(
            default_user_provider,
            default_login_provider,
            default_response_builder,
            default_token_payload_builder,
            security_context_manager_service,
            default_token_service
        )

    @Bean()
    @ConditionalOnMissingBean(IRegisterService)
    def default_register_service(self, db: DBManagerService, default_security_entity_configuration: SecurityEntityConfiguration) -> IRegisterService:
        """只有当用户没有定义自己的 IRegisterService Bean 时，才创建这个默认实例。"""
        return DefaultRegisterService(db, default_security_entity_configuration)

    @Bean()
    @ConditionalOnMissingBean(IUserManagerService)
    def default_user_manager_service(
            self,
            db: DBManagerService,
            default_security_entity_configuration: SecurityEntityConfiguration,
            default_token_service: ITokenService
    ) -> IUserManagerService:
        """只有当用户没有定义自己的 IUserManagerService Bean 时，才创建这个默认实例。"""
        return DefaultUserManagerService(db, default_security_entity_configuration, default_token_service)

    @Bean()
    def authentication_providers(self) -> List[IRequestAuthenticationProvider]:
        """Create authentication providers from config."""
        # 移除 default_token_service 依赖，在 Factory 内部懒加载
        return AuthProviderFactory.create_providers_from_config(token_manager=None)
