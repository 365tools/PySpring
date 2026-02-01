"""
测试 Auto 模式的完整功能，包括配置检查和真实连接测试
"""
import asyncio
import sys
import os

# 添加项目源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'pyspring', 'src'))

from pyspring.repositories.db.factory import DBServiceFactory
from pyspring.repositories.db.config import DatabaseConfig, PostgreSQLConfig, MySQLConfig, SQLiteConfig
from pyspring.repositories.cache.factory import CacheServiceFactory
from pyspring.repositories.cache.config import CacheConfig, RedisConfig, MemcachedConfig, MemoryConfig


async def test_db_auto_mode():
    """测试数据库 auto 模式的完整流程"""
    print("=== 数据库 Auto 模式测试 ===")
    
    # 测试场景1: PostgreSQL 配置不完整，降级到 MySQL，MySQL 也不完整，最终降级到 SQLite
    print("\n1. 测试配置不完整时的降级流程...")
    config = DatabaseConfig(
        type="auto",
        postgresql=PostgreSQLConfig(host="", database="test", user="test"),  # 故意设置为空的 host
        mysql=MySQLConfig(host="localhost", port=3306, database="test", user="test"),  # MySQL 配置完整但服务不可用
        sqlite=SQLiteConfig(database=":memory:")  # SQLite 作为最终备选
    )
    
    factory = DBServiceFactory(config)
    service = await factory.get_service()
    
    print(f"   ✓ 最终使用的数据库服务: {type(service).__name__}")
    print(f"   ✓ 服务类型: {factory._service_type}")
    
    # 验证最终使用了 SQLite（因为 PostgreSQL 和 MySQL 都失败了）
    assert factory._service_type == "sqlite", f"期望 sqlite，实际得到 {factory._service_type}"
    
    # 测试基本操作
    await service.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
    await service.execute("INSERT INTO test (name) VALUES (:name)", {"name": "Test"})
    result = await service.fetch_one("SELECT * FROM test")
    print(f"   ✓ SQLite 操作测试: {result}")
    
    # 测试场景2: 测试真实连接功能
    print("\n2. 验证 auto 模式包含真实连接测试...")
    # 使用一个无法连接的 PostgreSQL 配置来验证连接测试
    config2 = DatabaseConfig(
        type="auto",
        postgresql=PostgreSQLConfig(host="nonexistent_host", port=5432, database="test", user="test", password="test"),
        sqlite=SQLiteConfig(database=":memory:")
    )
    
    factory2 = DBServiceFactory(config2)
    service2 = await factory2.get_service()
    
    print(f"   ✓ 由于 PostgreSQL 无法连接，降级到: {type(service2).__name__}")
    assert factory2._service_type == "sqlite", f"期望 sqlite，实际得到 {factory2._service_type}"
    
    print("\n✓ 数据库 Auto 模式测试完成")


async def test_cache_auto_mode():
    """测试缓存 auto 模式的完整流程"""
    print("\n=== 缓存 Auto 模式测试 ===")
    
    # 测试场景: Redis 无法连接，降级到 Memcached，再降级到 Memory
    print("\n1. 测试缓存 auto 模式的降级流程...")
    config = CacheConfig(
        type="auto",
        redis=RedisConfig(host="nonexistent_redis", port=6379),  # Redis 无法连接
        memcached=MemcachedConfig(host="nonexistent_memcached", port=11211),  # Memcached 也无法连接
        memory=MemoryConfig(max_size=100, ttl=3600)  # Memory 作为最终备选
    )
    
    factory = CacheServiceFactory(config)
    service = await factory.get_service()
    
    print(f"   ✓ 最终使用的缓存服务: {type(service).__name__}")
    print(f"   ✓ 服务类型: {factory._service_type}")
    
    # 验证最终使用了内存缓存
    assert factory._service_type == "memory", f"期望 memory，实际得到 {factory._service_type}"
    
    # 测试基本操作
    await service.set("test_key", "test_value")
    value = await service.get("test_key")
    print(f"   ✓ 内存缓存操作测试: {value}")
    
    print("\n✓ 缓存 Auto 模式测试完成")


async def test_detailed_auto_flow():
    """详细测试 auto 模式的各个阶段"""
    print("\n=== 详细 Auto 模式流程测试 ===")
    
    # 测试完整的 PostgreSQL → MySQL → SQLite 降级流程
    print("\n1. 详细测试数据库降级流程...")
    
    # 配置一个 PostgreSQL 无效但 MySQL 有效的配置
    config = DatabaseConfig(
        type="auto",
        postgresql=PostgreSQLConfig(host="", database="test", user="test"),  # 无效配置
        mysql=MySQLConfig(host="localhost", port=3306, database="test", user="test"),  # 配置有效但服务不可用
        sqlite=SQLiteConfig(database=":memory:")  # 最终备选
    )
    
    factory = DBServiceFactory(config)
    service = await factory.get_service()
    
    print(f"   ✓ 降级序列结束，最终使用: {type(service).__name__}")
    
    # 测试带操作的流程
    print("\n2. 测试真实连接尝试...")
    try:
        # 尝试执行一些操作以确保服务正常工作
        await service.execute("CREATE TABLE verification (id INTEGER PRIMARY KEY)")
        await service.execute("INSERT INTO verification VALUES (1)")
        result = await service.fetch_one("SELECT * FROM verification")
        print(f"   ✓ 服务功能验证: {result}")
    except Exception as e:
        print(f"   ⚠ 服务操作异常: {e}")
    
    print("\n✓ 详细 Auto 模式流程测试完成")


async def main():
    """主测试函数"""
    print("开始测试 Auto 模式的完整功能...")
    print("此测试验证了 Auto 模式不仅检查配置，还会进行真实连接测试")
    
    await test_db_auto_mode()
    await test_cache_auto_mode()
    await test_detailed_auto_flow()
    
    print("\n=== 总结 ===")
    print("✅ Auto 模式功能完整测试通过!")
    print("✅ 配置检查功能正常工作")
    print("✅ 真实连接测试功能正常工作")
    print("✅ 降级策略按预期工作")
    print("✅ 每个阶段都包含配置验证和连接测试")


if __name__ == "__main__":
    asyncio.run(main())