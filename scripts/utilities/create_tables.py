"""
强制创建所有数据库表
"""
import asyncio

from pyspring.log.instance import logger
from pyspring.repositories.db.models.common.define import Base
from sqlalchemy.ext.asyncio import create_async_engine


async def create_tables():
    """创建所有数据库表"""
    logger.info("=" * 80)
    logger.info("🚀 开始创建数据库表")
    logger.info("=" * 80)

    # 创建数据库引擎
    engine = create_async_engine(
        "sqlite+aiosqlite:///data/app.db",
        echo=True  # 显示 SQL 语句
    )

    logger.info(f"\n📊 准备创建 {len(Base.metadata.tables)} 个表:")
    for table_name in sorted(Base.metadata.tables.keys()):
        logger.info(f"  - {table_name}")

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("\n" + "=" * 80)
    logger.info("✅ 数据库表创建成功！")
    logger.info("=" * 80)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
