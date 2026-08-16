"""关闭处理器管理"""
from abc import ABC, abstractmethod

from pyspring.core.ioc.interfaces.core import ILifecycle, IManaged
from pyspring.core.log.instance import logger


class IShutdownHandler(IManaged, ILifecycle, ABC):
    """
    关闭处理器接口
    
    用于在应用关闭时执行清理任务，如：
    - 关闭数据库连接
    - 释放资源
    - 保存状态
    
    使用方法：
    1. 继承 IShutdownHandler（自动包含 ILifecycle）
    2. 实现 shutdown() 方法
    3. 实现 get_name() 方法
    """

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        执行关闭逻辑
        
        Returns:
            bool: 关闭是否成功
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        获取处理器名称
        
        Returns:
            str: 处理器名称
        """
        pass

    async def on_startup(self):
        """ILifecycle 接口实现 - 关闭处理器无需启动初始化"""
        pass

    async def on_shutdown(self):
        """ILifecycle 接口实现 - 自动调用 shutdown()"""
        await self.execute()

    async def execute(self) -> bool:
        """
        执行关闭（带日志和错误处理）
        
        Returns:
            bool: 执行是否成功
        """
        try:
            logger.debug(f"🔄 开始执行关闭处理器: {self.get_name()}")
            result = await self.shutdown()
            if result:
                logger.debug(f"✅ 关闭处理器 [{self.get_name()}] 执行成功")
            else:
                logger.warning(f"⚠️  关闭处理器 [{self.get_name()}] 执行失败")
            return result
        except Exception as e:
            logger.error(f"❌ 关闭处理器 [{self.get_name()}] 执行异常: {e}", exc_info=True)
            return False


class ShutdownHandlerManager:
    """
    关闭处理器管理器
    
    自动发现和管理所有IShutdownHandler
    """

    def __init__(self, container):
        self.container = container
        self._handlers: list[IShutdownHandler] = []

    def discover(self):
        """发现所有关闭处理器"""
        logger.debug("🔍 搜索关闭处理器...")

        try:
            self._handlers = self.container.get_all_of_type(IShutdownHandler)
            logger.debug(f"📋 发现 {len(self._handlers)} 个关闭处理器")
        except ValueError:
            logger.debug("未发现任何关闭处理器")
            self._handlers = []

    async def execute_all(self) -> bool:
        """
        执行所有关闭处理器
        
        Returns:
            bool: 是否全部成功
        """
        if not self._handlers:
            logger.debug("⏭️  没有需要执行的关闭处理器")
            return True

        logger.debug(f"🔄 开始执行 {len(self._handlers)} 个关闭处理器...")

        success_count = 0
        # 反向执行（与初始化相反的顺序）
        for handler in reversed(self._handlers):
            try:
                result = await handler.execute()
                if result:
                    success_count += 1
            except Exception as e:
                logger.error(f"关闭处理器执行异常: {e}")

        all_success = success_count == len(self._handlers)
        if all_success:
            logger.debug(f"✅ 所有关闭处理器执行完成 ({success_count}/{len(self._handlers)})")
        else:
            logger.warning(f"⚠️  部分关闭处理器执行失败 ({success_count}/{len(self._handlers)})")

        return all_success


__all__ = ['IShutdownHandler', 'ShutdownHandlerManager']
