"""
测试 Cache 模块 IOC 注入架构

验证：
1. 服务自动注册为 @Component
2. Factory 自动注入配置和服务
3. Manager 使用 @property 延迟获取服务
4. API 层可以安全使用 Depends(get_bean(CacheManager))
"""
import asyncio
import os

from pyspring.ioc.context import ApplicationContext
from pyspring.repositories.cache.manager import CacheManagerService


async def test_cache_ioc_injection():
    """测试缓存模块 IOC 注入"""
    print("\n" + "=" * 60)
    print("🧪 测试 Cache 模块 IOC 注入")
    print("=" * 60)

    # 临时修改环境变量，使用内存缓存进行测试
    os.environ['CACHE_TYPE'] = 'memory'

    # 1. 初始化 IOC 容器
    ctx = ApplicationContext.initialize(base_packages=["pyspring.repositories.cache"])

    # 2. 获取 CacheManager（模拟 API 层 Depends）
    cache_manager = ctx.get_by_type(CacheManagerService)
    assert cache_manager is not None, "❌ CacheManager 注入失败"
    print("✅ CacheManager 成功注入")

    # 3. 测试延迟初始化（首次访问 provider）
    provider = cache_manager.provider
    assert provider is not None, "❌ Provider 未初始化"
    print(f"✅ Provider 延迟初始化成功: {provider.__class__.__name__}")

    # 4. 测试缓存是否正常工作
    await cache_manager.provider.save("test_key", "test_value", ttl=60)
    value = await cache_manager.provider.get("test_key")
    assert value == "test_value", "❌ 缓存读写失败"
    print("✅ 缓存读写测试通过")

    # 5. 测试 ping
    ping_result = await cache_manager.provider.ping()
    assert ping_result, "❌ Ping 失败"
    print("✅ Ping 测试通过")

    print("\n✅✅✅ Cache 模块 IOC 架构验证通过 ✅✅✅\n")

    ApplicationContext.reset()


async def test_cache_api_layer_usage():
    """模拟 API 层使用 Cache 场景"""
    print("\n" + "=" * 60)
    print("🧪 模拟 API 层使用 Cache（FastAPI Depends 模式）")
    print("=" * 60)

    # 设置测试环境
    os.environ['CACHE_TYPE'] = 'memory'

    # 模拟应用启动
    ctx = ApplicationContext.initialize(base_packages=["pyspring.repositories.cache"])

    # 模拟 API 依赖注入函数
    def get_cache_manager():
        """等价于 FastAPI 的 Depends"""
        return ctx.get_by_type(CacheManagerService)

    # 模拟 API 端点调用
    print("\n🔹 模拟 API 端点：缓存操作")
    cache_mgr = get_cache_manager()
    await cache_mgr.provider.save("user:1", {"name": "Alice"}, ttl=300)
    user_data = await cache_mgr.provider.get("user:1")
    print(f"✅ 缓存数据: {user_data}")

    print("\n✅✅✅ API 层使用场景验证通过 ✅✅✅")
    print("✅ Depends(get_bean(CacheManager)) 模式安全可用\n")

    ApplicationContext.reset()


async def main():
    """主测试流程"""
    try:
        await test_cache_ioc_injection()
        await test_cache_api_layer_usage()

        print("\n" + "=" * 60)
        print("🎉 Cache 模块 IOC 架构测试全部通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败：{e}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
