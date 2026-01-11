"""
关闭处理器接口

提供应用关闭时执行清理任务的基类
"""
from abc import ABC, abstractmethod

from pyspring.log.instance import logger


class IShutdownHandler(ABC):
    """
    关闭处理器基类
    
    用于在应用关闭时执行清理任务，如：
    - 关闭数据库连接
    - 关闭缓存连接
    - 释放资源
    - 保存状态
    等
    """

    def __init__(self, enabled: bool = True):
        """
        Args:
            enabled: 是否启用该关闭处理器
        """
        self.enabled = enabled

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
        获取关闭处理器名称
        
        Returns:
            str: 关闭处理器名称
        """
        pass

    async def execute(self) -> bool:
        """
        执行关闭处理（带日志和错误处理）
        
        Returns:
            bool: 执行是否成功
        """
        if not self.enabled:
            logger.debug(f"⏭️  关闭处理器 [{self.get_name()}] 已禁用，跳过")
            return True

        try:
            logger.info(f"🔄 开始执行关闭处理器: {self.get_name()}")
            result = await self.shutdown()
            if result:
                logger.info(f"✅ 关闭处理器 [{self.get_name()}] 执行成功")
            else:
                logger.warning(f"⚠️  关闭处理器 [{self.get_name()}] 执行失败")
            return result
        except Exception as e:
            logger.error(f"❌ 关闭处理器 [{self.get_name()}] 执行异常: {e}", exc_info=True)
            return False


class ShutdownHandlerManager:
    """
    关闭处理器管理器
    
    管理和执行所有关闭处理器
    """

    def __init__(self):
        self.handlers: list[IShutdownHandler] = []

    def register(self, handler: IShutdownHandler):
        """
        注册关闭处理器
        
        Args:
            handler: 关闭处理器实例
        """
        self.handlers.append(handler)
        logger.debug(f"📝 已注册关闭处理器: {handler.get_name()}")

    async def execute_all(self, stop_on_failure: bool = False) -> bool:
        """
        执行所有关闭处理器
        
        Args:
            stop_on_failure: 是否在某个处理器失败时停止执行（默认不停止，确保资源尽可能清理）
            
        Returns:
            bool: 是否所有处理器都成功执行
        """
        if not self.handlers:
            logger.debug("📭 没有注册的关闭处理器")
            return True

        logger.info(f"🔄 开始执行 {len(self.handlers)} 个关闭处理器...")

        success_count = 0
        failed_handlers = []

        for handler in self.handlers:
            result = await handler.execute()
            if result:
                success_count += 1
            else:
                failed_handlers.append(handler.get_name())
                if stop_on_failure:
                    logger.error(f"❌ 关闭处理器 [{handler.get_name()}] 失败，停止执行")
                    break

        # 报告执行结果
        total = len(self.handlers)
        if success_count == total:
            logger.info(f"✅ 所有关闭处理器执行成功 ({success_count}/{total})")
            return True
        else:
            logger.warning(f"⚠️  部分关闭处理器执行失败 ({success_count}/{total} 成功)")
            if failed_handlers:
                logger.warning(f"   失败的处理器: {', '.join(failed_handlers)}")
            return False
