"""启动初始化器管理"""

from abc import ABC, abstractmethod

from pyspring.core.ioc.interfaces.core import ILifecycle, IManaged
from pyspring.core.log.instance import logger


class IStartupInitializer(IManaged, ILifecycle, ABC):
    """
    启动初始化器接口

    用于在应用启动时执行初始化任务，如：
    - 数据库表结构初始化
    - 缓存预热
    - 配置验证
    - 数据迁移

    使用方法：
    1. 继承 IStartupInitializer（自动包含 ILifecycle）
    2. 实现 initialize() 方法
    3. 实现 get_name() 方法
    """

    def __init__(self, enabled: bool = True):
        """
        Args:
            enabled: 是否启用该初始化器
        """
        self.enabled = enabled

    @abstractmethod
    async def initialize(self) -> bool:
        """
        执行初始化逻辑

        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        获取初始化器名称

        Returns:
            str: 初始化器名称
        """
        pass

    async def on_startup(self):
        """ILifecycle 接口实现 - 自动调用 execute()"""
        await self.execute()

    async def on_shutdown(self):
        """ILifecycle 接口实现 - 初始化器无需关闭清理"""
        pass

    async def execute(self) -> bool:
        """
        执行初始化（带日志和错误处理）

        Returns:
            bool: 执行是否成功
        """
        if not self.enabled:
            logger.debug(f"⏭️  初始化器 [{self.get_name()}] 已禁用，跳过")
            return True

        try:
            logger.debug(f"🚀 开始执行初始化器: {self.get_name()}")
            result = await self.initialize()
            if result:
                logger.debug(f"✅ 初始化器 [{self.get_name()}] 执行成功")
            else:
                logger.warning(f"⚠️  初始化器 [{self.get_name()}] 执行失败")
            return result
        except Exception as e:
            logger.error(f"❌ 初始化器 [{self.get_name()}] 执行异常: {e}", exc_info=True)
            return False


class StartupInitializerManager:
    """
    启动初始化器管理器

    自动发现和管理所有IStartupInitializer
    """

    def __init__(self, container):
        self.container = container
        self._initializers: list[IStartupInitializer] = []

    def discover(self):
        """发现所有初始化器"""
        logger.debug("🔍 搜索启动初始化器...")

        # 获取所有IStartupInitializer类型的服务
        try:
            self._initializers = self.container.get_all_of_type(IStartupInitializer)
            logger.debug(f"📋 发现 {len(self._initializers)} 个初始化器")
        except ValueError:
            # 没有找到任何初始化器
            logger.debug("未发现任何初始化器")
            self._initializers = []

    async def execute_all(self) -> bool:
        """
        执行所有初始化器

        Returns:
            bool: 是否全部成功
        """
        if not self._initializers:
            logger.debug("⏭️  没有需要执行的初始化器")
            return True

        logger.debug(f"🚀 开始执行 {len(self._initializers)} 个初始化器...")

        success_count = 0
        for initializer in self._initializers:
            try:
                result = await initializer.execute()
                if result:
                    success_count += 1
            except Exception as e:
                logger.error(f"初始化器执行异常: {e}")

        all_success = success_count == len(self._initializers)
        if all_success:
            logger.debug(f"✅ 所有初始化器执行完成 ({success_count}/{len(self._initializers)})")
        else:
            logger.warning(f"⚠️  部分初始化器执行失败 ({success_count}/{len(self._initializers)})")

        return all_success


__all__ = ["IStartupInitializer", "StartupInitializerManager"]
