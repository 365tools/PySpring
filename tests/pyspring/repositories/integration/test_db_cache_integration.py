"""
数据库和缓存集成测试
"""
import pytest
import asyncio
from typing import Any

from pyspring.repositories.db.factory import DBServiceFactory
from pyspring.repositories.db.config import DatabaseConfig, SQLiteConfig
from pyspring.repositories.cache.factory import CacheServiceFactory
from pyspring.repositories.cache.config import CacheConfig, MemoryConfig
from pyspring.repositories.service import IDBService, ICacheService


class TestDBCacheIntegration:
    """数据库和缓存集成测试类"""
    
    @pytest.mark.asyncio
    async def test_basic_db_operations_with_cache(self):
        """测试基本数据库操作与缓存集成"""
        # 创建SQLite数据库配置
        db_config = DatabaseConfig(
            type="sqlite",
            sqlite=SQLiteConfig(database=":memory:")
        )
        db_factory = DBServiceFactory(db_config)
        db_service = await db_factory.get_service()
        
        # 创建内存缓存配置
        cache_config = CacheConfig(type="memory")
        cache_factory = CacheServiceFactory(cache_config)
        cache_service = await cache_factory.get_service()
        
        # 创建一个简单的表
        await db_service.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)
        
        # 插入数据
        await db_service.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            {"name": "John Doe", "email": "john@example.com"}
        )
        
        # 从数据库获取数据
        user = await db_service.fetch_one(
            "SELECT * FROM users WHERE email = ?",
            {"email": "john@example.com"}
        )
        
        assert user is not None
        assert user["name"] == "John Doe"
        
        # 将数据存储到缓存
        cache_key = f"user:{user['id']}"
        await cache_service.set(cache_key, user, ttl=3600)
        
        # 从缓存获取数据
        cached_user = await cache_service.get(cache_key)
        assert cached_user is not None
        assert cached_user["name"] == "John Doe"
        
        # 验证缓存和数据库数据一致性
        assert user == cached_user
        
        print("✓ 数据库和缓存基本操作测试通过")
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """测试并发访问"""
        # 创建服务
        db_config = DatabaseConfig(type="sqlite", sqlite=SQLiteConfig(database=":memory:"))
        db_factory = DBServiceFactory(db_config)
        db_service = await db_factory.get_service()
        
        cache_config = CacheConfig(type="memory")
        cache_factory = CacheServiceFactory(cache_config)
        cache_service = await cache_factory.get_service()
        
        # 创建表
        await db_service.execute("""
            CREATE TABLE IF NOT EXISTS counters (
                id TEXT PRIMARY KEY,
                value INTEGER DEFAULT 0
            )
        """)
        
        # 并发任务：多次增加计数器
        async def increment_counter(counter_id: str, increments: int):
            for i in range(increments):
                # 从数据库获取当前值
                result = await db_service.fetch_one(
                    "SELECT value FROM counters WHERE id = ?", 
                    {"id": counter_id}
                )
                
                if result:
                    new_value = result["value"] + 1
                    await db_service.execute(
                        "UPDATE counters SET value = ? WHERE id = ?",
                        {"value": new_value, "id": counter_id}
                    )
                else:
                    await db_service.execute(
                        "INSERT INTO counters (id, value) VALUES (?, ?)",
                        {"id": counter_id, "value": 1}
                    )
                
                # 更新缓存
                await cache_service.set(f"counter:{counter_id}", new_value if result else 1)
                
                await asyncio.sleep(0.001)  # 模拟一些处理时间
        
        # 并发执行多个任务
        tasks = [
            increment_counter("counter1", 10),
            increment_counter("counter2", 10),
            increment_counter("counter3", 10)
        ]
        
        await asyncio.gather(*tasks)
        
        # 验证结果
        for i in range(1, 4):
            counter_id = f"counter{i}"
            
            # 检查数据库中的值
            result = await db_service.fetch_one(
                "SELECT value FROM counters WHERE id = ?",
                {"id": counter_id}
            )
            assert result is not None
            assert result["value"] == 10  # 应该是10，因为每个计数器被增加了10次
            
            # 检查缓存中的值
            cached_value = await cache_service.get(f"counter:{counter_id}")
            assert cached_value == 10
        
        print("✓ 并发访问测试通过")
    
    @pytest.mark.asyncio
    async def test_factory_singleton_behavior(self):
        """测试工厂单例行为"""
        # 创建配置
        db_config = DatabaseConfig(type="sqlite", sqlite=SQLiteConfig(database=":memory:"))
        cache_config = CacheConfig(type="memory")
        
        # 创建多个工厂实例（通过IOC容器，这里模拟）
        db_factory1 = DBServiceFactory(db_config)
        db_factory2 = DBServiceFactory(db_config)
        
        cache_factory1 = CacheServiceFactory(cache_config)
        cache_factory2 = CacheServiceFactory(cache_config)
        
        # 获取服务
        db_service1 = await db_factory1.get_service()
        db_service2 = await db_factory1.get_service()  # 同一工厂
        db_service3 = await db_factory2.get_service()  # 不同工厂但相同配置
        
        cache_service1 = await cache_factory1.get_service()
        cache_service2 = await cache_factory1.get_service()  # 同一工厂
        cache_service3 = await cache_factory2.get_service()  # 不同工厂但相同配置
        
        # 验证同一工厂内的单例行为
        assert db_service1 is db_service2  # 同一工厂，应为同一实例
        assert cache_service1 is cache_service2  # 同一工厂，应为同一实例
        
        # 注意：不同工厂即使配置相同，也会创建不同的服务实例
        # 这是预期行为，因为工厂本身是独立的
        
        print("✓ 工厂单例行为测试通过")
    
    @pytest.mark.asyncio
    async def test_cache_fallback_mechanism(self):
        """测试缓存降级机制"""
        # 测试auto模式下的降级
        cache_config = CacheConfig(
            type="auto",
            redis=MemoryConfig(max_size=100),  # 使用内存配置模拟失败的Redis
            memcached=MemoryConfig(max_size=100),  # 使用内存配置模拟失败的Memcached
            memory=MemoryConfig(max_size=100, ttl=3600)
        )
        
        cache_factory = CacheServiceFactory(cache_config)
        
        # 由于Redis和Memcached配置不正确，应该降级到内存缓存
        cache_service = await cache_factory.get_service()
        
        # 验证服务可用
        await cache_service.set("test_key", "test_value", ttl=10)
        value = await cache_service.get("test_key")
        
        assert value == "test_value"
        
        # 验证类型（尽管配置了auto，但实际使用的类型取决于降级结果）
        print(f"✓ 缓存降级机制测试通过，实际使用类型: {type(cache_service).__name__}")