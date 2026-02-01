"""
缓存工厂功能测试
"""
import pytest
from unittest.mock import Mock

from pyspring.repositories.cache.factory import CacheServiceFactory
from pyspring.repositories.cache.config import CacheConfig, RedisConfig, MemoryConfig, MemcachedConfig


class TestCacheServiceFactory:
    """缓存服务工厂测试类"""
    
    def test_factory_initialization(self):
        """测试工厂初始化"""
        config = Mock(spec=CacheConfig)
        factory = CacheServiceFactory(config)
        
        assert factory.config == config
        assert factory._service is None
        assert factory._service_type is None
        assert isinstance(factory._service_creators, dict)
        assert len(factory._service_creators) == 3  # redis, memory, memcached
    
    @pytest.mark.asyncio
    async def test_get_memory_service(self):
        """测试获取内存缓存服务"""
        # 创建配置
        config = CacheConfig(type="memory")
        
        factory = CacheServiceFactory(config)
        
        # 获取服务
        service = await factory.get_service()
        
        # 验证服务类型和单例特性
        assert service is not None
        assert factory._service_type == "memory"
        
        # 再次获取应返回相同实例（单例测试）
        service2 = await factory.get_service()
        assert service is service2
    
    @pytest.mark.asyncio
    async def test_get_redis_service(self):
        """测试获取Redis缓存服务"""
        # 创建配置
        config = CacheConfig(
            type="redis",
            redis=RedisConfig(
                host="localhost",
                port=6379,
                db=0
            )
        )
        
        factory = CacheServiceFactory(config)
        
        # 获取服务
        service = await factory.get_service()
        
        # 验证服务类型和单例特性
        assert service is not None
        assert factory._service_type == "redis"
        
        # 再次获取应返回相同实例（单例测试）
        service2 = await factory.get_service()
        assert service is service2
    
    @pytest.mark.asyncio
    async def test_get_memcached_service(self):
        """测试获取Memcached缓存服务"""
        # 创建配置
        config = CacheConfig(
            type="memcached",
            memcached=MemcachedConfig(
                host="localhost",
                port=11211
            )
        )
        
        factory = CacheServiceFactory(config)
        
        # 获取服务
        service = await factory.get_service()
        
        # 验证服务类型和单例特性
        assert service is not None
        assert factory._service_type == "memcached"
        
        # 再次获取应返回相同实例（单例测试）
        service2 = await factory.get_service()
        assert service is service2
    
    @pytest.mark.asyncio
    async def test_unsupported_type_error(self):
        """测试不支持的类型抛出异常"""
        config = CacheConfig(type="unsupported_type")
        factory = CacheServiceFactory(config)
        
        with pytest.raises(ValueError) as exc_info:
            await factory.get_service()
        
        assert "Unsupported cache type" in str(exc_info.value)
        assert "redis, memory, memcached, auto" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_auto_mode_fallback(self):
        """测试auto模式降级功能"""
        # 创建配置，auto模式会尝试redis然后降级
        config = CacheConfig(
            type="auto",
            redis=RedisConfig(host="nonexistent", port=6379),
            memcached=MemcachedConfig(host="localhost", port=11211),
            memory=MemoryConfig(max_size=100, ttl=3600)
        )
        
        factory = CacheServiceFactory(config)
        
        # 由于Redis连接失败，会降级到Memcached，如果Memcached也失败则到Memory
        service = await factory.get_service()
        
        # 验证至少获取到了一个服务实例
        assert service is not None
        
        # 验证单例特性
        service2 = await factory.get_service()
        assert service is service2