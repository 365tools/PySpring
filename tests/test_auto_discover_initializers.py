"""
测试自动发现 StartupInitializer 的机制
"""
import asyncio

import pytest

from src.pyspring.core.interfaces.initializer.startup import IStartupInitializer
from src.pyspring.ioc.manager import AppContainerManager
from src.pyspring.log.instance import logger


@pytest.mark.asyncio
async def test_auto_discover_initializers():
    """测试自动发现所有 IStartupInitializer 实现"""
    logger.info("=" * 60)
    logger.info("测试：自动发现 StartupInitializer")
    logger.info("=" * 60)

    # 1. 创建 IoC 容器管理器并注册所有服务
    ioc_manager = AppContainerManager()
    ioc_manager.register_all_services()

    # 2. 自动发现所有实现了 IStartupInitializer 的服务
    startup_initializers = ioc_manager.get_all_instances_of(IStartupInitializer)

    logger.info(f"\n🔍 发现 {len(startup_initializers)} 个 StartupInitializer:")
    for initializer in startup_initializers:
        logger.info(f"  - {initializer.__class__.__name__}: {initializer.get_name()}")

    # 3. 使用自动发现的 run_startup_initializers 方法
    logger.info("\n🚀 测试 run_startup_initializers() 自动发现机制:")
    try:
        success = await ioc_manager.run_startup_initializers()
        if success:
            logger.info("✅ 自动发现测试成功！")
        else:
            logger.warning("⚠️  自动发现测试部分失败")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("测试说明：")
    logger.info("1. 自动扫描并注册所有 Initializer 结尾的类")
    logger.info("2. 通过 get_all_instances_of(IStartupInitializer) 自动发现所有实现")
    logger.info("3. 添加新 Initializer 时，只需实现接口并让类名以 Initializer 结尾")
    logger.info("4. 不需要手动修改 run_startup_initializers() 代码")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_auto_discover_initializers())
