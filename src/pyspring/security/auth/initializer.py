"""
认证系统启动初始化器

负责在应用启动时初始化认证提供者链
"""
from pyspring.interfaces.ISingleton import ISingletonService
from pyspring.interfaces.IStartupInitializer import IStartupInitializer
from pyspring.log.loguru.ins import logger


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
            from pyspring.ioc.manager import AppContainerManager
            from pyspring.security.auth.impl.token import TokenManagerService

            container = AppContainerManager()
            token_manager = container.get(TokenManagerService)

            # 初始化认证提供者链
            from pyspring.security.auth.factory import AuthProviderFactoryHelper
            AuthProviderFactoryHelper.initialize_authentication_system(
                token_manager=token_manager
            )

            self.initialized = True
            logger.info("✅ 认证系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 认证系统初始化失败: {e}")
            import traceback
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
