"""
import traceback
from pyspring.security.authentication.interfaces.validator import ISecurityContextValidator
from pyspring.security.authentication.services.core.context import SecurityContextManagerService
from pyspring.security.authentication.core.chain import AuthenticationChain
from pyspring.security.core.config.loader import SecurityConfigManager
from pyspring.security.authentication.core.factory import AuthProviderFactory
from pyspring.security.authentication.services.session.token import TokenManagerService
from pyspring.ioc.manager import AppContainerManager

认证系统启动初始化器

负责在应用启动时初始化认证提供者链
"""
import traceback

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.ioc.manager import AppContainerManager
from pyspring.log.instance import logger
from pyspring.security.authentication.core.chain import AuthenticationChain
from pyspring.security.authentication.core.factory import AuthProviderFactory
from pyspring.security.authentication.interfaces.validator import ISecurityContextValidator
from pyspring.security.authentication.services.core.context import SecurityContextManagerService
from pyspring.security.authentication.services.session.token import TokenManagerService
from pyspring.security.core.config.loader import SecurityConfigManager


class AuthenticationInitializer(IStartupInitializer, ISingletonService):
    """
    认证系统启动初始化器
    
    在应用启动时自动执行，负责：
    1. 从配置文件读取认证提供者配置
    2. 创建认证提供者实例
    3. 注册到认证链
    """

    def __init__(self, enabled: bool = True):
        """
        初始化
        
        Args:
            enabled: 是否启用该初始化器
        """
        # 显式调用 IStartupInitializer 的 __init__
        IStartupInitializer.__init__(self, enabled)
        self.initialized = False

    async def initialize(self) -> bool:
        """
        初始化认证系统
        
        Returns:
            是否初始化成功
        """
        if self.initialized:
            logger.debug("⚠️ 认证系统已初始化，跳过")
            return True

        try:
            logger.info("🔐 正在初始化认证系统...")

            # 获取依赖服务

            container = AppContainerManager()
            token_manager = container.get(TokenManagerService)

            # 初始化认证提供者链
            # 注意: AuthProviderFactoryHelper 需要在 factory.py 中实现或在此处实现逻辑

            config_manager = SecurityConfigManager()
            providers_config = config_manager.get_authentication_providers()

            # 使用 AuthProviderFactory 创建提供者
            providers = []
            # providers_config 是 List[Dict]，直接遍历
            for config in providers_config:
                if not config.get("enabled", True):
                    continue

                # 确保 config 中包含 name
                name = config.get("name", "unknown")

                provider = AuthProviderFactory.create_provider(
                    provider_config=config,
                    token_manager=token_manager
                )
                if provider:
                    providers.append(provider)

            # 注册到认证链
            auth_chain = container.get(AuthenticationChain)
            auth_chain.register_providers(providers)

            # [Auto-Discovery] 自动发现并注册安全上下文验证器
            # 这使得开发者只需编写 Validator 并继承 ISingletonService，无需手动注册

            # 使用 container.get() 确保服务已初始化
            context_manager = container.get(SecurityContextManagerService)

            # 扫描所有 ISecurityContextValidator 的实现
            validators = container.get_all_instances_of(ISecurityContextValidator)

            if validators:
                for v in validators:
                    context_manager.register(v)
                logger.debug(f"🔍 自动注册了 {len(validators)} 个安全上下文验证器: {[v.name for v in validators]}")
            else:
                logger.debug("🔍 未发现自定义安全上下文验证器")

            self.initialized = True
            logger.info("✅ 认证系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 认证系统初始化失败: {e}")
            logger.error(traceback.format_exc())
            return False

    def get_priority(self) -> int:
        """
        获取初始化器优先级
        
        Returns:
            优先级（数字越小越先执行）
            认证系统需要在其他系统之前初始化，所以优先级设为 10
        """
        return 10

    def get_name(self) -> str:
        """
        获取初始化器名称
        
        Returns:
            初始化器名称
        """
        return "AuthenticationInitializer"


__all__ = ['AuthenticationInitializer']
