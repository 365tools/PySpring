"""
Cache 模块重构验证测试

验证以下功能：
1. YAML 配置自动加载
2. IOC 依赖注入
3. Cache 服务初始化
4. Redis/Memory 服务切换
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from pyspring.ioc.context import ApplicationContext
from pyspring.repositories.cache.config import CacheConfig
from pyspring.repositories.cache.manager import CacheManagerService
from pyspring.repositories.cache.initializer.connection import CacheConnectionInitializer


async def test_yaml_config_loading():
    """测试 YAML 配置自动加载"""
    print("\n" + "=" * 60)
    print("测试 1: YAML 配置自动加载")
    print("=" * 60)

    # 直接创建 CacheConfig 实例（会自动加载 YAML）
    config = CacheConfig()

    print(f"✅ 缓存类型: {config.type}")
    print(f"✅ Redis 主机: {config.redis.host}:{config.redis.port}")
    print(f"✅ Redis 连接池: max_connections={config.redis.pool.max_connections}")
    print(f"✅ 内存缓存: max_size={config.memory.max_size}, ttl={config.memory.ttl}")

    assert config.type in ["redis", "memory", "auto"]
    print("\n✅ YAML 配置加载测试通过！")


async def test_ioc_injection():
    """测试 IOC 依赖注入"""
    print("\n" + "=" * 60)
    print("测试 2: IOC 依赖注入")
    print("=" * 60)

    # 强制导入 Initializer 确保被扫描
    from pyspring.repositories.cache.initializer.connection import CacheConnectionInitializer as _  # noqa

    # 初始化 IOC 容器（明确扫描initializer包）
    context = ApplicationContext.initialize(base_packages=[
        "pyspring.repositories.cache",
        "pyspring.repositories.cache.initializer",  # 明确包含 initializer
    ])

    # 打印扫描到的所有组件
    print(f"\n扫描到的组件列表：")
    for service_name in context.container.registry._definitions.keys():
        print(f"  - {service_name}")
    print()

    # 从容器获取 CacheConfig（应该是单例）
    config1 = context.get_by_type(CacheConfig)
    config2 = context.get_by_type(CacheConfig)

    assert config1 is config2, "CacheConfig 应该是单例"
    print(f"✅ CacheConfig 单例验证通过: {id(config1) == id(config2)}")

    # 从容器获取 CacheManagerService（应该是单例）
    manager1 = context.get_by_type(CacheManagerService)
    manager2 = context.get_by_type(CacheManagerService)

    assert manager1 is manager2, "CacheManagerService 应该是单例"
    print(f"✅ CacheManagerService 单例验证通过: {id(manager1) == id(manager2)}")

    # 获取 Initializer（应该自动注入了 config 和 manager）
    initializer = context.get_by_type(CacheConnectionInitializer)

    assert initializer.cache_config is not None, "Initializer 应该注入了 CacheConfig"
    assert initializer.cache_manager is not None, "Initializer 应该注入了 CacheManagerService"

    print(f"✅ Initializer 依赖注入验证通过")
    print(f"   - cache_config: {type(initializer.cache_config).__name__}")
    print(f"   - cache_manager: {type(initializer.cache_manager).__name__}")

    print("\n✅ IOC 依赖注入测试通过！")


async def test_cache_initialization():
    """测试 Cache 服务初始化"""
    print("\n" + "=" * 60)
    print("测试 3: Cache 服务初始化")
    print("=" * 60)

    context = ApplicationContext.get_instance()

    # 获取 Initializer 并执行启动初始化
    initializer = context.get_by_type(CacheConnectionInitializer)
    success = await initializer.startup()

    assert success, "Cache 初始化应该成功"
    print(f"✅ Cache 初始化成功: {success}")

    # 获取 Manager 并验证 provider 已设置
    manager = context.get_by_type(CacheManagerService)
    provider = manager.get_provider()

    print(f"✅ 缓存提供者: {type(provider).__name__}")

    # 测试 ping
    ping_result = await provider.ping()
    assert ping_result, "Ping 应该成功"
    print(f"✅ Ping 测试通过: {ping_result}")

    print("\n✅ Cache 服务初始化测试通过！")


async def test_cache_operations():
    """测试 Cache 基本操作"""
    print("\n" + "=" * 60)
    print("测试 4: Cache 基本操作")
    print("=" * 60)

    context = ApplicationContext.get_instance()
    manager = context.get_by_type(CacheManagerService)
    cache = manager.current

    # 测试 set/get
    test_key = "test:key:1"
    test_value = {"name": "PySpring", "version": "1.0.0"}

    await cache.set(test_key, test_value, ex=60)
    print(f"✅ SET: {test_key} = {test_value}")

    retrieved = await cache.get(test_key)
    assert retrieved == test_value, "获取的值应该与设置的值相同"
    print(f"✅ GET: {test_key} = {retrieved}")

    # 测试 exists
    exists = await cache.exists(test_key)
    assert exists, "键应该存在"
    print(f"✅ EXISTS: {test_key} = {exists}")

    # 测试 delete
    deleted = await cache.delete(test_key)
    assert deleted, "删除应该成功"
    print(f"✅ DELETE: {test_key} = {deleted}")

    # 验证删除
    exists_after = await cache.exists(test_key)
    assert not exists_after, "删除后键不应该存在"
    print(f"✅ EXISTS (after delete): {test_key} = {exists_after}")

    print("\n✅ Cache 基本操作测试通过！")


async def test_cleanup():
    """测试清理资源"""
    print("\n" + "=" * 60)
    print("测试 5: 清理资源")
    print("=" * 60)

    context = ApplicationContext.get_instance()
    manager = context.get_by_type(CacheManagerService)

    await manager.close()
    print("✅ Cache 连接已关闭")

    print("\n✅ 清理资源测试通过！")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("Cache 模块重构验证测试")
    print("=" * 80)

    try:
        # 测试 1: YAML 配置加载
        await test_yaml_config_loading()

        # 测试 2: IOC 依赖注入
        await test_ioc_injection()

        # 测试 3: Cache 服务初始化
        await test_cache_initialization()

        # 测试 4: Cache 基本操作
        await test_cache_operations()

        # 测试 5: 清理资源
        await test_cleanup()

        print("\n" + "=" * 80)
        print("✅ 所有测试通过！Cache 模块重构成功！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
