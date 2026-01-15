"""
from pyspring.security.authentication.core.chain import AuthenticationChain
from pyspring.ioc.manager import AppContainerManager

认证提供者工厂
根据配置动态创建认证提供者实例
"""
from typing import Dict, Type, List

from pyspring.ioc.manager import AppContainerManager
from pyspring.log.instance import logger
from pyspring.security.authentication.core.chain import AuthenticationChain
from pyspring.security.authentication.providers.base import BaseAuthenticationProvider
from pyspring.security.authentication.providers.jwt import JWTAuthenticationProvider
from pyspring.security.authentication.services.session.token import TokenManagerService
from pyspring.security.core.config.loader import SecurityConfigManager


class AuthProviderFactory:
    """认证提供者工厂"""

    # 提供者类型映射表
    _provider_registry: Dict[str, Type[BaseAuthenticationProvider]] = {
        "JWTAuthProvider": JWTAuthenticationProvider,
        # 可以在这里注册更多的提供者类型
        # "APIKeyAuthProvider": APIKeyAuthProvider,
        # "OAuth2AuthProvider": OAuth2AuthProvider,
    }

    @classmethod
    def register_provider_type(cls, provider_type: str, provider_class: Type[BaseAuthenticationProvider]):
        """
        注册自定义认证提供者类型
        
        Args:
            provider_type: 提供者类型名称（与配置文件中的 type 字段对应）
            provider_class: 提供者类
        """
        cls._provider_registry[provider_type] = provider_class
        logger.info(f"✅ 注册自定义认证提供者类型: {provider_type}")

    @classmethod
    def create_provider(
            cls,
            provider_config: dict,
            token_manager: TokenManagerService = None,
            **kwargs
    ) -> BaseAuthenticationProvider:
        """
        根据配置创建认证提供者实例
        
        Args:
            provider_config: 提供者配置（从 security.yaml 读取）
            token_manager: Token 管理服务（JWT 提供者需要）
            **kwargs: 其他依赖服务
            
        Returns:
            BaseAuthenticationProvider: 认证提供者实例
            
        Raises:
            ValueError: 未知的提供者类型
        """
        provider_type = provider_config.get("type")
        provider_name = provider_config.get("name", provider_type)

        if provider_type not in cls._provider_registry:
            raise ValueError(f"未知的认证提供者类型: {provider_type}")

        provider_class = cls._provider_registry[provider_type]

        # 根据提供者类型传递不同的依赖
        if provider_type == "JWTAuthProvider":
            if token_manager is None:
                raise ValueError("JWTAuthProvider 需要 TokenManagerService 依赖")
            return provider_class(provider_name, provider_config, token_manager)

        # 其他提供者类型的创建逻辑
        # elif provider_type == "APIKeyAuthProvider":
        #     return provider_class(provider_name, provider_config, api_key_service)

        # 默认创建方式
        return provider_class(provider_name, provider_config)

    @classmethod
    def create_providers_from_config(
            cls,
            token_manager: TokenManagerService = None,
            **kwargs
    ) -> List[BaseAuthenticationProvider]:
        """
        从配置文件创建所有认证提供者
        
        Args:
            token_manager: Token 管理服务
            **kwargs: 其他依赖服务
            
        Returns:
            List[BaseAuthenticationProvider]: 认证提供者列表
        """
        config_manager = SecurityConfigManager()
        providers_config = config_manager.get_providers_config()

        providers = []
        failed_providers = []  # 记录失败的提供者

        for provider_config in providers_config:
            provider_name = provider_config.get('name')
            provider_type = provider_config.get('type')

            try:
                provider = cls.create_provider(
                    provider_config,
                    token_manager=token_manager,
                    **kwargs
                )
                providers.append(provider)
                logger.info(f"✅ 创建认证提供者: {provider.get_name()} ({provider_type})")
            except ValueError as e:
                # 未知的提供者类型（可能是未实现的功能），使用 WARNING 级别
                failed_providers.append((provider_name, provider_type, str(e)))
                logger.warning(f"⚠️  跳过认证提供者: {provider_name} ({provider_type}) - {e}")
            except Exception as e:
                # 其他错误（如配置错误、依赖缺失），使用 ERROR 级别
                failed_providers.append((provider_name, provider_type, str(e)))
                logger.error(f"❌ 创建认证提供者失败: {provider_name} - {e}")

        # 只有当一个提供者都没创建成功时，才报 ERROR
        if not providers and failed_providers:
            logger.error(f"❌ 所有认证提供者创建失败！已配置 {len(failed_providers)} 个提供者，但无一成功")
            for name, ptype, error in failed_providers:
                logger.error(f"   - {name} ({ptype}): {error}")
        elif providers and failed_providers:
            logger.info(f"ℹ️  已创建 {len(providers)} 个认证提供者，跳过 {len(failed_providers)} 个未实现的提供者")

        return providers


class AuthProviderFactoryHelper:
    """
    认证提供者工厂辅助类
    
    提供便捷的静态方法来初始化认证系统
    """

    @staticmethod
    def initialize_authentication_system(
            token_manager: TokenManagerService,
            **kwargs
    ) -> None:
        """
        初始化认证系统
        
        步骤：
        1. 从配置文件读取提供者配置
        2. 创建所有认证提供者实例
        3. 注册到认证链
        
        Args:
            token_manager: Token 管理服务
            **kwargs: 其他依赖服务
        """
        # 注意：AppContainerManager 依赖整个安全模块，必须局部导入以打破循环

        logger.info("🚀 开始初始化认证提供者")

        # 1. 创建提供者
        providers = AuthProviderFactory.create_providers_from_config(
            token_manager=token_manager,
            **kwargs
        )

        if not providers:
            logger.warning("⚠️  未创建任何认证提供者，使用默认配置")
            # 创建默认的 JWT 提供者
            default_config = {
                "name": "jwt",
                "type": "JWTAuthProvider",
                "enabled": True,
                "priority": 1,
                "config": {
                    "token_sources": ["header", "cookie", "query"],
                    "token_prefix": "Bearer"
                }
            }
            default_provider = AuthProviderFactory.create_provider(
                default_config,
                token_manager=token_manager
            )
            providers.append(default_provider)

        # 2. 注册到认证链（通过 IoC 容器获取）
        container = AppContainerManager()
        chain = container.get(AuthenticationChain)
        chain.register_providers(providers)

        logger.info(f"✅ 认证系统初始化完成，共 {len(providers)} 个提供者")

    @staticmethod
    def register_custom_provider(provider_type: str, provider_class: Type[BaseAuthenticationProvider]):
        """
        注册自定义认证提供者
        
        Args:
            provider_type: 提供者类型名称
            provider_class: 提供者类
        """
        AuthProviderFactory.register_provider_type(provider_type, provider_class)
