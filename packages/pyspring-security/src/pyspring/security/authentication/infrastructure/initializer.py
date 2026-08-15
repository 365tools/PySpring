"""
认证系统启动初始化器
"""
import traceback

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.context import ApplicationContext
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.ioc.lifecycle.initializer import IStartupInitializer
from pyspring.core.log.instance import logger
from pyspring.security.authentication.contracts.request_auth import IRequestAuthenticationProvider
from pyspring.security.authentication.services.context_validator import SecurityContextManagerService
from .chain import AuthenticationChain
from ..contracts.validator import ISecurityContextValidator


@Component
@Singleton
class AuthenticationInitializer(IStartupInitializer, IManaged):
    """
    认证系统启动初始化器（由IOC容器管理单例）
    
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
            logger.debug("[Warning] 认证系统已初始化，跳过")
            return True

        try:
            logger.info("[Security] 正在初始化认证系统...")

            # 动态获取容器
            container = ApplicationContext.get_instance()

            # 1. 动态获取并注册认证提供者到认证链
            try:
                # 优先尝试从@Bean方法获取providers列表
                authentication_providers = None
                if container.container.has("authentication_providers"):
                    authentication_providers = container.get("authentication_providers")
                    logger.debug(f"[Debug] 从@Bean获取到 {len(authentication_providers) if authentication_providers else 0} 个认证提供者")

                # 降级：从IoC容器中查找所有IRequestAuthenticationProvider实现
                if not authentication_providers:
                    authentication_providers = container.get_all_instances_of(IRequestAuthenticationProvider)
                    logger.debug(f"[Debug] 从IoC容器扫描到 {len(authentication_providers)} 个认证提供者")
                
                if authentication_providers:
                    self.auth_chain.register_providers(authentication_providers)
                    logger.info(f"[Success] 注册了 {len(authentication_providers)} 个认证提供者: "
                                 f"{[p.__class__.__name__ for p in authentication_providers]}")
                else:
                    logger.debug("[Debug] 未发现任何认证提供者（如果不使用认证功能，这是正常的）")
            except Exception as e:
                logger.warning(f"[Warning] 获取认证提供者失败: {e}")

            # 2. 动态获取并注册安全上下文验证器
            try:
                validators = container.get_all_instances_of(ISecurityContextValidator)
                if validators:
                    for v in validators:
                        self.context_manager.register(v)
                    logger.debug(f"[Debug] 自动注册了 {len(validators)} 个安全上下文验证器: {[v.__class__.__name__ for v in validators]}")
                else:
                    logger.debug("[Debug] 未发现自定义安全上下文验证器")
            except Exception as e:
                logger.warning(f"[Warning] 获取安全上下文验证器失败: {e}")

            self.initialized = True
            logger.info("[Success] 认证系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"[Error] 认证系统初始化失败: {e}")
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
