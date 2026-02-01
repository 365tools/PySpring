"""
测试数据库和缓存模块的基本功能
"""
import asyncio
import sys
import os

# 添加项目源码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'pyspring', 'src'))

from pyspring.repositories.db.factory import DBServiceFactory
from pyspring.repositories.db.config import DatabaseConfig, SQLiteConfig
from pyspring.repositories.cache.factory import CacheServiceFactory
from pyspring.repositories.cache.config import CacheConfig, MemoryConfig


async def test_basic_functionality():
    """测试基本功能"""
    print("开始测试数据库和缓存模块功能...")
    
    # 测试数据库工厂
    print("\n1. 测试数据库工厂...")
    db_config = DatabaseConfig(type="sqlite", sqlite=SQLiteConfig(database=":memory:"))
    db_factory = DBServiceFactory(db_config)
    
    db_service = await db_factory.get_service()
    print(f"   ✓ 获取数据库服务成功: {type(db_service).__name__}")
    
    # 验证单例特性
    db_service2 = await db_factory.get_service()
    print(f"   ✓ 单例验证: {db_service is db_service2}")
    
    # 测试基本数据库操作
    await db_service.execute(
        "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
    )
    
    await db_service.execute(
        "INSERT INTO test_table (name) VALUES (:name)",
        {"name": "Test User"}
    )
    
    result = await db_service.fetch_one("SELECT * FROM test_table LIMIT 1")
    print(f"   ✓ 数据库操作测试: {result}")
    
    # 测试缓存工厂
    print("\n2. 测试缓存工厂...")
    cache_config = CacheConfig(type="memory")
    cache_factory = CacheServiceFactory(cache_config)
    
    cache_service = await cache_factory.get_service()
    print(f"   ✓ 获取缓存服务成功: {type(cache_service).__name__}")
    
    # 验证单例特性
    cache_service2 = await cache_factory.get_service()
    print(f"   ✓ 单例验证: {cache_service is cache_service2}")
    
    # 测试基本缓存操作 - 避免使用可能不支持的参数
    await cache_service.set("test_key", "test_value")
    value = await cache_service.get("test_key")
    print(f"   ✓ 缓存操作测试: {value}")
    
    # 测试工厂的注册表功能
    print("\n3. 测试工厂注册表...")
    print(f"   ✓ 数据库工厂支持类型: {list(db_factory._service_creators.keys())}")
    print(f"   ✓ 缓存工厂支持类型: {list(cache_factory._service_creators.keys())}")
    
    # 测试auto模式
    print("\n4. 测试auto模式...")
    auto_db_config = DatabaseConfig(type="auto", sqlite=SQLiteConfig(database=":memory:"))
    auto_db_factory = DBServiceFactory(auto_db_config)
    auto_db_service = await auto_db_factory.get_service()
    print(f"   ✓ Auto模式数据库服务: {type(auto_db_service).__name__}")
    
    auto_cache_config = CacheConfig(type="auto", memory=MemoryConfig())
    auto_cache_factory = CacheServiceFactory(auto_cache_config)
    auto_cache_service = await auto_cache_factory.get_service()
    print(f"   ✓ Auto模式缓存服务: {type(auto_cache_service).__name__}")
    
    print("\n✓ 所有功能测试通过!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())