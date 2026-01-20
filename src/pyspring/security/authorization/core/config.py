from pyspring.ioc.annotations.decorators import Configuration, Bean, ConditionalOnMissingBean
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.core.component import SecurityEntityConfiguration
from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.role import IRoleProvider
from pyspring.security.authorization.contracts.rule import IPathPermissionProvider
from pyspring.security.authorization.implementations.role.database import DefaultRoleProvider
from pyspring.security.authorization.implementations.rule.config import DefaultPathPermissionProvider
from pyspring.security.authorization.services.flow.check import DefaultPermissionService
from pyspring.security.core.config.loader import SecurityConfigManager


@Configuration
class AuthorizationConfiguration:
    """
    授权模块自动配置
    """

    @Bean
    @ConditionalOnMissingBean(IRoleProvider)
    def default_role_provider(self, db_manager: DBManagerService, component: SecurityEntityConfiguration) -> IRoleProvider:
        """注册默认的角色提供者 (基于数据库)"""
        return DefaultRoleProvider(db_manager, component)

    @Bean
    @ConditionalOnMissingBean(IPathPermissionProvider)
    def default_path_permission_provider(self, config_manager: SecurityConfigManager) -> IPathPermissionProvider:
        """注册默认的路径权限提供者 (基于配置)"""
        return DefaultPathPermissionProvider(config_manager)

    @Bean
    @ConditionalOnMissingBean(IPermissionService)
    def default_permission_service(self, role_provider: IRoleProvider) -> IPermissionService:
        """注册默认的权限服务"""
        return DefaultPermissionService(role_provider)
