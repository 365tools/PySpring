"""
验证数据库表结构是否正确
"""
import asyncio

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine


async def verify_schema():
    """验证数据库表结构"""
    # 直接创建数据库引擎
    engine = create_async_engine(
        "sqlite+aiosqlite:///data/app.db",
        echo=False
    )

    print("=" * 60)
    print("🔍 检查数据库表结构")
    print("=" * 60)

    async with engine.begin() as conn:
        def check_schema(sync_conn):
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()

            print(f"\n📊 数据库中的表 ({len(tables)} 个):")
            for table in sorted(tables):
                print(f"  - {table}")

            # 检查关键表的字段
            if 'pyspring_user_role' in tables:
                print("\n🔎 pyspring_user_role 表结构:")
                columns = inspector.get_columns('pyspring_user_role')
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                print("\n❌ pyspring_user_role 表不存在")

            if 'pyspring_role_permission' in tables:
                print("\n🔎 pyspring_role_permission 表结构:")
                columns = inspector.get_columns('pyspring_role_permission')
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                print("\n❌ pyspring_role_permission 表不存在")

        await conn.run_sync(check_schema)

    await engine.dispose()

    print("\n" + "=" * 60)
    print("✅ 数据库表结构验证完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(verify_schema())
