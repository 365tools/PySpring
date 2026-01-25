"""
认证模块自动配置

使用最新的IOC框架，配置所有默认的认证组件
"""
from typing import List

from pyspring.ioc.annotations import Configuration, Bean, ConditionalOnMissingBean
from pyspring.log.instance import logger
# 导入配置和工厂
# 导入接口
from pyspring.security.authentication.contracts.login import ILoginProvider
from pyspring.security.authentication.contracts.request_auth import IRequestAuthenticationProvider
from pyspring.security.authentication.contracts.token import ITokenService
from pyspring.security.authentication.factories.auth_provider.factory import AuthProviderFactory
# 导入默认实现
from pyspring.security.authentication.providers.login.password import DefaultPasswordLoginProvider
from pyspring.security.core.config.loader import SecurityConfigManager


@Configuration
class AuthenticationConfiguration:
    """
    PySpring 安全模块(认证部分)的自动配置。
    
    设计理念：
    1. 只包含真正需要编排/组装的 Bean（如 List 类型、工厂方法）
    2. 简单的默认实现类都使用 @ConditionalOnMissingBean 装饰器，自动扫描
    3. 用户可以通过提供自己的实现类来替换任何默认实现
    
    自动扫描的默认组件：
    - SecurityConfigManager (IManaged) - 安全配置管理器
    - SecurityEntityConfiguration (IManaged) - 实体映射配置
    - BCryptPasswordEncoder (IPasswordEncoder) - 密码加密
    - DefaultUserProvider (IUserProvider) - 用户查询
    - DefaultPasswordLoginProvider (ILoginProvider) - 密码登录
    - DefaultResponseBuilder (IResponseBuilder) - 响应构建
    - DefaultLoginService (ILoginService) - 登录服务
    - DefaultRegisterService (IRegisterService) - 注册服务
    - DefaultUserManagerService (IUserManagerService) - 用户管理
    - TokenService (ITokenService) - Token 管理
    - DefaultTokenPayloadBuilder (ITokenPayloadBuilder) - Token 载荷构建
    
    需要 @Bean 注册的：
    - default_login_providers - 返回 List
    - authentication_providers - 工厂方法
    """

    @Bean()
    @ConditionalOnMissingBean(ILoginProvider)
    def default_login_providers(self, default_password_login_provider: DefaultPasswordLoginProvider) -> List[ILoginProvider]:
        """
        组装默认的认证提供者列表
        
        为什么需要 @Bean？
        - 返回类型是 List，无法用单个类表示
        - 需要组装多个 Provider（当前只有密码登录，未来可能有 OAuth2, LDAP 等）
        - 用户可以注册多个 ILoginProvider Bean，系统会自动收集
        """
        return [default_password_login_provider]

    @Bean()
    def authentication_providers(
            self,
            config_manager: SecurityConfigManager,
            token_service: ITokenService
    ) -> List[IRequestAuthenticationProvider]:
        """
        使用工厂方法创建认证提供者列表
        
        为什么需要 @Bean？
        - 返回类型是 List
        - 使用工厂方法，根据配置动态创建（JWT, Basic Auth 等）
        - 需要从 config 文件读取配置
        
        参数说明:
        - config_manager: IOC自动注入SecurityConfigManager，确保配置已加载
        - token_service: IOC自动注入ITokenService，用于JWT提供者
        """
        providers = AuthProviderFactory.create_providers_from_config(
            token_manager=token_service,
            config_manager=config_manager
        )
        if not providers:
            logger.warning("[Config] 未创建任何认证提供者，请检查 security.yaml 配置或查看上方的错误日志")
        return providers
