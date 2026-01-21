"""
认证系统启动初始化器
"""
import traceback

from pyspring.ioc.manager import AppContainerManager

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.log.instance import logger
from pyspring.security.authentication.implementations.request.base import BaseAuthenticationProvider as IAuthenticationProvider
from pyspring.security.authentication.services.context_validator import SecurityContextManagerService
from .chain import AuthenticationChain
from ..interfaces.validator import ISecurityContextValidator


class AuthenticationInitializer(IStartupInitializer, ISingletonService):
    """
    认证系统启动初始化器
    
    在应用启动时自动执行，负责：
    1. 收集 IoC 容器中所有可用的认证提供者，并注册到认证链。
    2. 收集 IoC 容器中所有可用的安全上下文验证器，并注册到安全上下文管理器。
    """

    def __init__(
            self,
            auth_chain: AuthenticationChain,
            context_manager: SecurityContextManagerService,
            enabled: bool = True
    ):
        """
        初始化（移除List注入，改为在initialize()中动态获取，避免循环依赖）
        
        Args:
            auth_chain: 认证链管理器
            context_manager: 安全上下文管理器
            enabled: 是否启用该初始化器
        """
        IStartupInitializer.__init__(self, enabled)
        self.auth_chain = auth_chain
        self.context_manager = context_manager
        self.initialized = False

    async def initialize(self) -> bool:
        """
        初始化认证系统（动态获取依赖，避免循环依赖）
        
        Returns:
            是否初始化成功
        """
        if self.initialized:
            logger.debug("⚠️ 认证系统已初始化，跳过")
            return True

        try:
            logger.info("🔐 正在初始化认证系统...")

            # 动态获取容器
            container = AppContainerManager()

            # 1. 动态获取并注册认证提供者到认证链
            try:
                authentication_providers = container.get_all_instances_of(IAuthenticationProvider)
                if authentication_providers:
                    self.auth_chain.register_providers(authentication_providers)
                    logger.debug(f"🔍 注册了 {len(authentication_providers)} 个认证提供者: "
                                 f"{[p.__class__.__name__ for p in authentication_providers]}")
                else:
                    logger.warning("⚠️ 未发现任何认证提供者，认证系统可能无法正常工作。")
            except Exception as e:
                logger.warning(f"⚠️ 获取认证提供者失败: {e}")

            # 2. 动态获取并注册安全上下文验证器
            try:
                validators = container.get_all_instances_of(ISecurityContextValidator)
                if validators:
                    for v in validators:
                        self.context_manager.register(v)
                    logger.debug(f"🔍 自动注册了 {len(validators)} 个安全上下文验证器: {[v.__class__.__name__ for v in validators]}")
                else:
                    logger.debug("🔍 未发现自定义安全上下文验证器")
            except Exception as e:
                logger.warning(f"⚠️ 获取安全上下文验证器失败: {e}")

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
