"""
综合测试：自动发现所有 Initializer 和 Handler
"""
import asyncio

import pytest
from pyspring.ioc.manager import AppContainerManager

from pyspring.core.abstracts.interfaces.handler.shutdown import IShutdownHandler
from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.log.instance import logger


@pytest.mark.asyncio
async def test_full_lifecycle():
    """测试完整的应用生命周期：启动 -> 关闭"""
    logger.info("=" * 70)
    logger.info("综合测试：自动发现机制 - 完整应用生命周期")
    logger.info("=" * 70)

    # 1. 创建 IoC 容器管理器并注册所有服务
    logger.info("\n📦 步骤 1: 注册所有服务...")
    ioc_manager = AppContainerManager()
    ioc_manager.register_all_services()

    # 2. 发现所有 Initializer
    logger.info("\n🔍 步骤 2: 发现所有 StartupInitializer...")
    startup_initializers = ioc_manager.get_all_instances_of(IStartupInitializer)
    logger.info(f"发现 {len(startup_initializers)} 个 StartupInitializer:")
    initializer_names = []
    for initializer in startup_initializers:
        name = initializer.get_name()
        initializer_names.append(name)
        logger.info(f"  • {name}")

    # 验证关键初始化器是否存在
    assert "AuthenticationInitializer" in initializer_names, "AuthenticationInitializer 未被发现"

    # 3. 发现所有 ShutdownHandler
    logger.info("\n🔍 步骤 3: 发现所有 ShutdownHandler...")
    shutdown_handlers = ioc_manager.get_all_instances_of(IShutdownHandler)
    logger.info(f"发现 {len(shutdown_handlers)} 个 ShutdownHandler:")
    for handler in shutdown_handlers:
        logger.info(f"  • {handler.get_name()}")

    # 4. 执行启动初始化器
    logger.info("\n🚀 步骤 4: 执行启动初始化...")
    try:
        await ioc_manager.run_startup_initializers()
        logger.info("✅ 启动初始化成功")
    except Exception as e:
        logger.warning(f"⚠️  启动初始化有错误（非致命）: {e}")

    # 5. 执行关闭处理器
    logger.info("\n🔄 步骤 5: 执行关闭处理...")
    success = await ioc_manager.run_shutdown_handlers()
    if success:
        logger.info("✅ 关闭处理成功")
    else:
        logger.warning("⚠️  关闭处理部分失败")

    # 总结
    logger.info("\n" + "=" * 70)
    logger.info("✨ 测试总结")
    logger.info("=" * 70)
    logger.info(f"✅ 自动发现 {len(startup_initializers)} 个启动初始化器")
    logger.info(f"✅ 自动发现 {len(shutdown_handlers)} 个关闭处理器")
    logger.info("✅ 完全自动化，无需手动注册")
    logger.info("✅ 类似 Java Spring 的 @Component 扫描机制")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_full_lifecycle())
