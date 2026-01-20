"""
启动初始化器接口

提供应用启动时执行初始化任务的基类
"""
from abc import ABC, abstractmethod

from pyspring.log.instance import logger
from ..ISingleton import ISingletonService


class IStartupInitializer(ISingletonService, ABC):
    """
    启动初始化器基类
    
    用于在应用启动时执行初始化任务，如：
    - 数据库表结构初始化
    - 缓存预热
    - 配置验证
    - 数据迁移
    等
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
                logger.info(f"✅ 初始化器 [{self.get_name()}] 执行成功")
            else:
                logger.warning(f"⚠️  初始化器 [{self.get_name()}] 执行失败")
            return result
        except Exception as e:
            logger.error(f"❌ 初始化器 [{self.get_name()}] 执行异常: {e}", exc_info=True)
            return False


class StartupInitializerManager:
    """
    启动初始化器管理器
    
    管理和执行所有启动初始化器
    """

    def __init__(self):
        self.initializers: list[IStartupInitializer] = []

    def register(self, initializer: IStartupInitializer):
        """
        注册初始化器
        
        Args:
            initializer: 初始化器实例
        """
        self.initializers.append(initializer)
        logger.debug(f"📝 已注册初始化器: {initializer.get_name()}")

    async def execute_all(self, stop_on_failure: bool = False) -> bool:
        """
        执行所有初始化器
        
        Args:
            stop_on_failure: 是否在某个初始化器失败时停止执行
            
        Returns:
            bool: 是否所有初始化器都成功
        """
        if not self.initializers:
            logger.debug("📭 没有注册的初始化器")
            return True

        logger.info(f"🎯 开始执行 {len(self.initializers)} 个初始化器")

        success_count = 0
        failed_count = 0

        for initializer in self.initializers:
            result = await initializer.execute()
            if result:
                success_count += 1
            else:
                failed_count += 1
                if stop_on_failure:
                    logger.error(f"🛑 初始化器失败，停止执行剩余初始化器")
                    break

        total = len(self.initializers)
        logger.info(f"📊 初始化器执行完成: 成功 {success_count}/{total}, 失败 {failed_count}/{total}")

        return failed_count == 0
