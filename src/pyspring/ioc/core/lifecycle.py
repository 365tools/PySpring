from pyspring.core.interfaces.handler.shutdown import IShutdownHandler, ShutdownHandlerManager
from pyspring.core.interfaces.initializer.startup import IStartupInitializer, StartupInitializerManager
from pyspring.log.instance import logger


class LifecycleManager:
    """
    生命周期管理器，负责应用的启动初始化和关闭处理
    """

    def __init__(self, container):
        self.container = container

    def get_all_instances_of(self, interface_type: type) -> list:
        """获取所有实现了指定接口的服务实例"""
        return self.container.get_instances_of_type(interface_type)

    async def run_startup_initializers(self):
        """
        在 IoC 扫描完成后，执行所有启动初始化器
        
        使用自动发现机制，无需手动注册每个具体的 Initializer
        只要服务实现了 IStartupInitializer 接口并注册到 IoC 容器，就会被自动发现和执行
        
        Returns:
            bool: 是否所有初始化器都成功
            
        Raises:
            RuntimeError: 如果关键初始化器失败
        """
        logger.info("🚀 开始执行启动初始化器...")

        try:
            # 创建初始化器管理器
            manager = StartupInitializerManager()

            # 自动发现所有实现了 IStartupInitializer 接口的服务
            # 类似 Java: List<IStartupInitializer> initializers = applicationContext.getBeansOfType(IStartupInitializer.class)
            startup_initializers = self.get_all_instances_of(IStartupInitializer)

            if not startup_initializers:
                logger.info("ℹ️  未发现任何启动初始化器")
                return True

            logger.info(f"🔍 发现 {len(startup_initializers)} 个启动初始化器")

            # 注册所有发现的初始化器
            for initializer in startup_initializers:
                manager.register(initializer)
                logger.debug(f"📝 已注册启动初始化器: {initializer.get_name()}")

            # 执行所有初始化器（失败时停止）
            success = await manager.execute_all(stop_on_failure=True)

            if not success:
                logger.error("❌ 启动初始化失败")
                raise RuntimeError("Startup initialization failed")

            logger.info("✅ 所有启动初始化器执行成功")
            return True

        except Exception as e:
            logger.error(f"🚨 启动初始化异常: {e}", exc_info=True)
            raise

    async def run_shutdown_handlers(self):
        """
        在应用关闭时，执行所有关闭处理器
        
        使用自动发现机制，无需手动注册每个具体的 ShutdownHandler
        只要服务实现了 IShutdownHandler 接口并注册到 IoC 容器，就会被自动发现和执行
        
        Returns:
            bool: 是否所有关闭处理器都成功
        """
        logger.info("🔄 开始执行关闭处理器...")

        try:
            # 创建关闭处理器管理器
            manager = ShutdownHandlerManager()

            # 自动发现所有实现了 IShutdownHandler 接口的服务
            # 类似 Java: List<IShutdownHandler> handlers = applicationContext.getBeansOfType(IShutdownHandler.class)
            shutdown_handlers = self.get_all_instances_of(IShutdownHandler)

            if not shutdown_handlers:
                logger.info("ℹ️  未发现任何关闭处理器")
                return True

            logger.info(f"🔍 发现 {len(shutdown_handlers)} 个关闭处理器")

            # 注册所有发现的处理器
            for handler in shutdown_handlers:
                manager.register(handler)
                logger.debug(f"📝 已注册关闭处理器: {handler.get_name()}")

            # 执行所有关闭处理器（不停止，确保所有资源都能清理）
            success = await manager.execute_all(stop_on_failure=False)

            if success:
                logger.info("✅ 所有关闭处理器执行成功")
            else:
                logger.warning("⚠️  部分关闭处理器执行失败")

            return success

        except Exception as e:
            logger.error(f"🚨 关闭处理异常: {e}", exc_info=True)
            return False
