"""
初始化数据库表结构
"""
import asyncio

from pyspring.ioc.context import ApplicationContext
from pyspring.log.instance import logger


async def init_database():
    """初始化数据库"""
    logger.info("=" * 80)
    logger.info("🚀 开始初始化数据库")
    logger.info("=" * 80)

    # 初始化 IoC 容器（会触发数据库表创建）
    ctx = ApplicationContext.initialize(
        base_packages=['pyspring'],
        enable_aop=False
    )
    logger.info("✅ IoC 容器初始化完成")

    # 初始化生命周期服务（包括数据库初始化）
    await ctx.container.initialize_lifecycle_services()
    logger.info("✅ 数据库初始化完成")

    # 关闭
    await ctx.container.destroy_lifecycle_services()

    logger.info("=" * 80)
    logger.info("✅ 数据库初始化成功，请运行 verify_db_schema.py 验证")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(init_database())
