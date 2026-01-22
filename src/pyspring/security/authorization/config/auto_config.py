"""
授权模块自动配置

参考authentication模块的结构，使用IOC框架配置授权组件
"""
from pyspring.ioc.annotations.component import Configuration, Bean, ConditionalOnMissingBean
from pyspring.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.config.entity.config import SecurityEntityConfiguration
from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.role import IRoleProvider
from pyspring.security.authorization.contracts.rule import IPathPermissionProvider
from pyspring.security.authorization.providers.permission.default import DefaultPermissionService
from pyspring.security.authorization.providers.role.database import DefaultRoleProvider
from pyspring.security.authorization.providers.rule.config import DefaultPathPermissionProvider
from pyspring.security.core.config.loader import SecurityConfigManager


@Configuration
class AuthorizationConfiguration:
    """
    PySpring 安全模块(授权部分)的默认自动配置
    
    架构设计：
    - IRoleProvider: 角色提供者，负责查询用户角色和角色权限
    - IPathPermissionProvider: 路径规则提供者，负责URL路径权限映射
    - IPermissionService: 权限服务，负责权限判定逻辑
    
    用户可以通过实现接口并注册@Bean来替换默认实现
    """

    def initialize(self):
        """配置初始化（可选）"""
        logger.info("[Authorization] 授权模块配置已加载")

    @Bean
    @ConditionalOnMissingBean(IRoleProvider)
    def default_role_provider(
            self,
            db_manager: DBManagerService,
            component: SecurityEntityConfiguration
    ) -> IRoleProvider:
        """
        注册默认的角色提供者（基于数据库）
        
        Args:
            db_manager: 数据库管理服务
            component: 安全实体配置（提供ORM模型）
            
        Returns:
            IRoleProvider: 角色提供者实例
        """
        logger.debug("[Authorization] 注册默认角色提供者: DefaultRoleProvider")
        return DefaultRoleProvider(db_manager, component)

    @Bean
    @ConditionalOnMissingBean(IPathPermissionProvider)
    def default_path_permission_provider(
            self,
            config_manager: SecurityConfigManager
    ) -> IPathPermissionProvider:
        """
        注册默认的路径权限规则提供者（基于配置文件）
        
        Args:
            config_manager: 安全配置管理器
            
        Returns:
            IPathPermissionProvider: 路径规则提供者实例
        """
        logger.debug("[Authorization] 注册默认路径权限提供者: DefaultPathPermissionProvider")
        return DefaultPathPermissionProvider(config_manager)

    @Bean
    @ConditionalOnMissingBean(IPermissionService)
    def default_permission_service(
            self,
            role_provider: IRoleProvider
    ) -> IPermissionService:
        """
        注册默认的权限服务
        
        Args:
            role_provider: 角色提供者（用于查询用户角色和权限）
            
        Returns:
            IPermissionService: 权限服务实例
        """
        logger.debug("[Authorization] 注册默认权限服务: DefaultPermissionService")
        return DefaultPermissionService(role_provider)
