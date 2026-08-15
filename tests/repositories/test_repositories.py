"""
pyspring-repositories：数据访问层测试

验证独立 repositories starter 的核心能力：
- 数据库配置模型（默认值、子配置）
- 缓存配置模型
- DB/Cache 服务接口契约
"""
import pytest

from pyspring.repositories.db.config import DatabaseConfig, DatabasePoolConfig, SQLiteConfig
from pyspring.repositories.db.service import IDBService
from pyspring.repositories.cache.config import CacheConfig, RedisConfig, MemoryConfig
from pyspring.repositories.cache.service import ICacheService


class TestDatabaseConfig:
    """数据库配置"""

    def test_default_sqlite(self):
        cfg = DatabaseConfig()
        assert cfg.type == "sqlite"
        assert cfg.sqlite.database == "data/app.db"

    def test_postgresql_defaults(self):
        cfg = DatabaseConfig(type="postgresql")
        assert cfg.type == "postgresql"
        assert cfg.postgresql.host == "localhost"
        assert cfg.postgresql.port == 5432

    def test_pool_config(self):
        pool = DatabasePoolConfig()
        assert pool.size == 5
        assert pool.max_overflow == 10
        assert pool.pre_ping is True

    def test_sqlite_config(self):
        cfg = SQLiteConfig(database=":memory:")
        assert cfg.database == ":memory:"


class TestCacheConfig:
    """缓存配置"""

    def test_default_memory(self):
        cfg = CacheConfig()
        assert cfg.type == "memory"
        assert cfg.memory.max_size == 1000

    def test_redis_defaults(self):
        cfg = CacheConfig(type="redis")
        assert cfg.type == "redis"
        assert cfg.redis.host == "localhost"
        assert cfg.redis.port == 6379

    def test_redis_pool(self):
        cfg = CacheConfig(type="redis")
        assert cfg.redis.pool.max_connections == 50


class MockDBService(IDBService):
    """mock DB 服务实现，验证接口契约"""
    async def execute(self, query, params=None):
        return None

    async def fetch_one(self, query, params=None):
        return {"id": 1}

    async def fetch_all(self, query, params=None):
        return [{"id": 1}, {"id": 2}]

    async def insert(self, table, data):
        return {"id": 1}

    async def engine(self):
        raise NotImplementedError

    async def session(self):
        raise NotImplementedError

    async def close(self):
        pass

    async def ping(self):
        return True


class TestDBInterfaceContract:
    """IDBService 接口契约"""

    def test_mock_is_db_service(self):
        svc = MockDBService()
        assert isinstance(svc, IDBService)

    @pytest.mark.asyncio
    async def test_fetch_all(self):
        svc = MockDBService()
        rows = await svc.fetch_all("SELECT * FROM t")
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_ping(self):
        svc = MockDBService()
        assert await svc.ping() is True


class MockCacheService(ICacheService):
    """mock 缓存服务实现，验证接口契约"""
    def __init__(self):
        self._store = {}

    async def get(self, key, default=None):
        return self._store.get(key, default)

    async def set(self, key, value):
        self._store[key] = value
        return True

    async def save(self, key, value):
        return await self.set(key, value)

    async def exists(self, key):
        return key in self._store

    async def update(self, key, value):
        self._store[key] = value
        return True

    async def delete(self, key):
        return self._store.pop(key, None) is not None

    async def clear(self):
        self._store.clear()

    async def ping(self):
        return True


class TestCacheInterfaceContract:
    """ICacheService 接口契约"""

    def test_mock_is_cache_service(self):
        svc = MockCacheService()
        assert isinstance(svc, ICacheService)

    @pytest.mark.asyncio
    async def test_set_get(self):
        svc = MockCacheService()
        await svc.set("key", "value")
        assert await svc.get("key") == "value"

    @pytest.mark.asyncio
    async def test_exists_delete(self):
        svc = MockCacheService()
        await svc.set("k", 1)
        assert await svc.exists("k") is True
        assert await svc.delete("k") is True
        assert await svc.exists("k") is False
