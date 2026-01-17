"""
测试自动发现 ShutdownHandler 的机制

类似 Java 中根据基类获取所有实现类的功能
"""
import asyncio

import pytest

from pyspring.core.abstracts.interfaces.handler.shutdown import IShutdownHandler
from pyspring.ioc.manager import AppContainerManager
from pyspring.log.instance import logger


@pytest.mark.asyncio
async def test_auto_discover():
    """测试自动发现所有 IShutdownHandler 实现"""
    logger.info("=" * 60)
    logger.info("测试：自动发现 ShutdownHandler")
    logger.info("=" * 60)

    # 1. 创建 IoC 容器管理器并注册所有服务
    ioc_manager = AppContainerManager()
    ioc_manager.register_all_services()

    # 2. 自动发现所有实现了 IShutdownHandler 的服务
    # 类似 Java: List<IShutdownHandler> handlers = applicationContext.getBeansOfType(IShutdownHandler.class)
    shutdown_handlers = ioc_manager.get_all_instances_of(IShutdownHandler)

    logger.info(f"\n🔍 发现 {len(shutdown_handlers)} 个 ShutdownHandler:")
    for handler in shutdown_handlers:
        logger.info(f"  - {handler.__class__.__name__}: {handler.get_name()}")

    # 3. 使用自动发现的 run_shutdown_handlers 方法
    logger.info("\n🔄 测试 run_shutdown_handlers() 自动发现机制:")
    success = await ioc_manager.run_shutdown_handlers()

    if success:
        logger.info("✅ 自动发现测试成功！")
    else:
        logger.warning("⚠️  自动发现测试部分失败")

    logger.info("\n" + "=" * 60)
    logger.info("测试说明：")
    logger.info("1. 自动扫描并注册所有 Handler 结尾的类")
    logger.info("2. 通过 get_all_instances_of(IShutdownHandler) 自动发现所有实现")
    logger.info("3. 添加新 ShutdownHandler 时，只需实现接口并让类名以 Handler 结尾")
    logger.info("4. 不需要手动修改 run_shutdown_handlers() 代码")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_auto_discover())
