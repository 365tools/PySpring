from pyspring.core.services.system import SystemService
from pyspring.ioc.annotations.decorators import Configuration, Bean, ConditionalOnMissingBean
from pyspring.repositories.cache.manager import CacheManagerService
# 导入其他依赖
from pyspring.repositories.db.manager import DBManagerService
# 导入接口和默认实现
from .component import SecurityEntityConfiguration
from .interfaces import (
    IUserProvider, IAuthenticationProvider, IResponseBuilder, ITokenPayloadBuilder,
    ITokenService, ILoginService, IRegisterService, IUserManagerService
)
from ..services.core.context import SecurityContextManagerService
from ..services.providers.auth import DefaultPasswordAuthenticationProvider
from ..services.providers.manager import AuthenticationProviderManager
from ..services.providers.response import DefaultResponseBuilder
from ..services.providers.token import DefaultTokenPayloadBuilder
from ..services.providers.user import DefaultUserProvider
from ..services.session.login import DefaultLoginService
from ..services.session.token import DefaultTokenManagerService
from ..services.user.manager import DefaultUserManagerService
from ..services.user.register import DefaultRegisterService


@Configuration
class DefaultSecurityConfiguration:
    """
    PySpring 安全模块的默认自动配置。
    负责注册所有默认的策略实现（Provider, Builder 等）。
    """

    @Bean
    @ConditionalOnMissingBean(SecurityEntityConfiguration)
    def default_security_component(self) -> SecurityEntityConfiguration:
        """Provide a default SecurityEntityConfiguration Bean if the user hasn't defined one."""
        return SecurityEntityConfiguration()

    @Bean
    @ConditionalOnMissingBean(IUserProvider)
    def default_user_provider(self, db: DBManagerService, component: SecurityEntityConfiguration) -> IUserProvider:
        """Create default instance if user defined IUserProvider Bean is missing."""
        return DefaultUserProvider(db, component)

    @Bean
    @ConditionalOnMissingBean(DefaultPasswordAuthenticationProvider)
    def password_authentication_provider(self, user_provider: IUserProvider, db: DBManagerService) -> DefaultPasswordAuthenticationProvider:
        """Create default PasswordAuthenticationProvider."""
        return DefaultPasswordAuthenticationProvider(user_provider, db)

    @Bean
    @ConditionalOnMissingBean(IAuthenticationProvider)
    def authentication_manager(self, password_provider: DefaultPasswordAuthenticationProvider) -> IAuthenticationProvider:
        """
        Create the main AuthenticationManager (which is also an IAuthenticationProvider).
        It manages a list of providers. By default, only password_provider is added.
        """
        return AuthenticationProviderManager([password_provider])

    @Bean
    @ConditionalOnMissingBean(IResponseBuilder)
    def default_response_builder(self, component: SecurityEntityConfiguration, system_service: SystemService) -> IResponseBuilder:
        """Create default instance if user defined IResponseBuilder Bean is missing."""
        return DefaultResponseBuilder(component, system_service)

    @Bean
    @ConditionalOnMissingBean(ITokenPayloadBuilder)
    def default_token_payload_builder(self, db: DBManagerService, component: SecurityEntityConfiguration) -> ITokenPayloadBuilder:
        """只有当用户没有定义自己的 ITokenPayloadBuilder Bean 时，才创建这个默认实例。"""
        return DefaultTokenPayloadBuilder(db, component)

    @Bean
    @ConditionalOnMissingBean(ITokenService)
    def default_token_service(self, system_service: SystemService, cache: CacheManagerService, db: DBManagerService) -> ITokenService:
        """只有当用户没有定义自己的 ITokenService Bean 时，才创建这个默认实例。"""
        return DefaultTokenManagerService(system_service, cache, db)

    @Bean
    @ConditionalOnMissingBean(ILoginService)
    def default_login_service(
            self,
            user_provider: IUserProvider,
            auth_provider: IAuthenticationProvider,
            token_manager: ITokenService,
            response_builder: IResponseBuilder,
            payload_builder: ITokenPayloadBuilder,
            context_manager: SecurityContextManagerService
    ) -> ILoginService:
        """只有当用户没有定义自己的 ILoginService Bean 时，才创建这个默认实例。"""
        return DefaultLoginService(
            user_provider,
            auth_provider,
            token_manager,
            response_builder,
            payload_builder,
            context_manager
        )

    @Bean
    @ConditionalOnMissingBean(IRegisterService)
    def default_register_service(self, db: DBManagerService, component: SecurityEntityConfiguration) -> IRegisterService:
        """只有当用户没有定义自己的 IRegisterService Bean 时，才创建这个默认实例。"""
        return DefaultRegisterService(db, component)

    @Bean
    @ConditionalOnMissingBean(IUserManagerService)
    def default_user_manager_service(self, db: DBManagerService, token_manager: ITokenService, component: SecurityEntityConfiguration) -> IUserManagerService:
        """只有当用户没有定义自己的 IUserManagerService Bean 时，才创建这个默认实例。"""
        return DefaultUserManagerService(db, token_manager, component)
