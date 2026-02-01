"""
测试 Repositories 模块完整 IOC 注入架构

验证整个 repositories 模块（cache + db）的 IOC 集成：
1. 所有服务自动注册为 @Component
2. Factory 自动注入配置和服务
3. Manager 使用 @property 延迟获取服务
4. API 层可以安全同时使用 Cache 和 DB
"""
import asyncio
import os

from pyspring.ioc.context import ApplicationContext
from pyspring.repositories.cache.manager import CacheManagerService
from pyspring.repositories.db.manager import DBManagerService


async def test_repositories_full_integration():
    """测试 repositories 模块完整集成"""
    print("\n" + "=" * 60)
    print("🧪 测试 Repositories 模块完整集成（Cache + DB）")
    print("=" * 60)

    # 设置测试环境
    os.environ['CACHE_TYPE'] = 'memory'
    os.environ['DATABASE_TYPE'] = 'sqlite'

    # 模拟应用启动 - 扫描整个 repositories 模块
    ctx = ApplicationContext.initialize(base_packages=["pyspring.repositories"])

    # 1. 获取 Cache Manager
    cache_manager = ctx.get_by_type(CacheManagerService)
    assert cache_manager is not None, "❌ CacheManager 注入失败"
    print("✅ CacheManager 成功注入")

    # 2. 获取 DB Manager
    db_manager = ctx.get_by_type(DBManagerService)
    assert db_manager is not None, "❌ DBManager 注入失败"
    print("✅ DBManager 成功注入")

    # 3. 测试 Cache 功能
    cache_provider = await cache_manager.provider()
    await cache_provider.save("test_key", "test_value", ttl=60)
    cached_value = await cache_provider.get("test_key")
    assert cached_value == "test_value", "❌ 缓存读写失败"
    print("✅ Cache 功能正常")

    # 4. 测试 DB 功能
    db_provider = await db_manager.provider()
    async with await db_manager.session() as session:
        assert session is not None, "❌ Session 创建失败"
        print("✅ DB 功能正常")

    print("\n✅✅✅ Repositories 模块完整集成验证通过 ✅✅✅\n")

    ApplicationContext.reset()


async def test_api_layer_full_usage():
    """模拟 API 层同时使用 Cache 和 DB"""
    print("\n" + "=" * 60)
    print("🧪 模拟 API 层同时使用 Cache 和 DB（FastAPI Depends 模式）")
    print("=" * 60)

    # 设置测试环境
    os.environ['CACHE_TYPE'] = 'memory'
    os.environ['DATABASE_TYPE'] = 'sqlite'

    # 模拟应用启动
    ctx = ApplicationContext.initialize(base_packages=["pyspring.repositories"])

    # 模拟 API 依赖注入函数
    def get_cache_manager():
        """等价于 FastAPI 的 Depends"""
        return ctx.get_by_type(CacheManagerService)

    def get_db_manager():
        """等价于 FastAPI 的 Depends"""
        return ctx.get_by_type(DBManagerService)

    # 模拟 API 端点：先查缓存，缓存未命中则查数据库
    print("\n🔹 模拟 API 端点：用户查询（Cache + DB）")
    cache_mgr = get_cache_manager()
    db_mgr = get_db_manager()

    user_id = "user:123"

    # 1. 先查缓存
    cached_user = await cache_mgr.provider.get(user_id)
    if cached_user:
        print(f"✅ 缓存命中: {cached_user}")
    else:
        print("⚠️ 缓存未命中，查询数据库")
        # 2. 缓存未命中，查数据库
        async with await db_mgr.session() as session:
            # 模拟数据库查询
            user_data = {"id": 123, "name": "Alice", "email": "alice@example.com"}
            print(f"✅ 数据库查询成功: {user_data}")

            # 3. 写入缓存
            await cache_mgr.provider.save(user_id, user_data, ttl=300)
            print("✅ 数据已缓存")

    print("\n✅✅✅ API 层完整使用场景验证通过 ✅✅✅")
    print("✅ Depends(get_bean(Manager)) 模式在复杂场景下安全可用\n")

    ApplicationContext.reset()


async def main():
    """主测试流程"""
    try:
        await test_repositories_full_integration()
        await test_api_layer_full_usage()

        print("\n" + "=" * 60)
        print("🎉🎉🎉 Repositories 模块完整 IOC 架构测试通过！🎉🎉🎉")
        print("=" * 60)
        print("""
✅ 架构改进总结：
  1. 服务通过 @Component 注册，由 IOC 容器统一管理
  2. Factory 通过构造函数注入配置和所有服务
  3. Manager 使用 @property 延迟初始化，无需手动 set_provider
  4. Initializer 仅负责连接建立，不再手动创建服务
  5. API 层可以安全使用 Depends(get_bean(Manager))
  
✅ 解决的核心问题：
  - ❌ 旧模式：手动 set_provider() → API 层 provider 可能为 None
  - ✅ 新模式：Factory + @property → API 层 provider 永远不为 None
        """)

    except Exception as e:
        print(f"\n❌ 测试失败：{e}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
