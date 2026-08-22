"""
缓存服务工厂（根据配置选择实现）
"""

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.log.instance import logger

from .config import CacheConfig
from .providers.memcached.services.service import MemcachedService
from .providers.memory.services.service import MemoryService
from .providers.redis.services.service import RedisService
from .service import ICacheService


@Component
@Singleton
class CacheServiceFactory:
    """缓存服务工厂（由 IOC 容器管理）"""

    def __init__(self, cache_config: CacheConfig):
        """
        通过 IOC 注入配置

        Args:
            cache_config: CacheConfig 实例（自动注入）
        """
        self.config: CacheConfig = cache_config
        self._service: (ICacheService) | None = None
        self._service_type: (str) | None = None

        # 注册所有支持的服务创建器（使用 lambda 实现延迟加载）
        self._service_creators = {
            "redis": lambda: self._create_redis_service(),
            "memory": lambda: self._create_memory_service(),
            "memcached": lambda: self._create_memcached_service(),
        }

    async def get_service(self) -> ICacheService:
        """
        根据配置返回正确的缓存服务（单例模式）

        Returns:
            ICacheService: Redis 或 Memory 实现
        """
        # 如果已创建，直接返回（单例）
        if self._service is not None:
            return self._service

        cache_type = self.config.type.lower()

        if cache_type in self._service_creators:
            self._service = self._service_creators[cache_type]()
            self._service_type = cache_type
        elif cache_type == "auto":
            # auto 模式：默认 Redis，失败降级到 Memcached，最后降级到 Memory
            logger.debug("CacheServiceFactory: Auto mode - trying Redis first...")
            self._service = await self._try_redis_or_memcached_or_fallback()
        else:
            available_types = list(self._service_creators.keys()) + ["auto"]
            raise ValueError(f"Unsupported cache type: {cache_type}. Available types: {', '.join(available_types)}.")

        assert self._service is not None, "CacheServiceFactory failed to create a service instance"
        return self._service

    def _create_redis_service(self) -> RedisService:
        """创建 Redis 服务"""
        logger.info("✅ 使用 Redis 缓存")
        return RedisService(self.config)

    def _create_memory_service(self) -> MemoryService:
        """创建 Memory 服务"""
        logger.info("✅ 使用内存缓存")
        return MemoryService(self.config)

    def _create_memcached_service(self) -> MemcachedService:
        """创建 Memcached 服务"""
        logger.info("✅ 使用 Memcached 缓存")
        return MemcachedService(self.config)

    async def _try_redis_or_memcached_or_fallback(self) -> ICacheService:
        """
        尝试连接 Redis，失败则降级到 Memcached，再失败则降级到内存缓存

        策略：
        1. 检查 Redis 配置完整性
        2. 创建 Redis 服务并执行 ping 测试
        3. Redis 测试成功：返回 Redis
        4. Redis 测试失败：尝试 Memcached
        5. Memcached 测试成功：返回 Memcached
        6. Memcached 测试失败：降级到内存缓存

        Returns:
            ICacheService: Redis、Memcached 或 Memory 服务（已测试可用）
        """
        redis_config = self.config.redis

        # 1. 检查 Redis 配置完整性
        if not redis_config.host:
            logger.warning("⚠️ Redis 配置不完整，尝试 Memcached...")
            return await self._try_memcached_or_fallback()

        # 2. 创建并测试 Redis 服务
        try:
            logger.info("🔍 Auto 模式：测试 Redis 连接...")
            service = RedisService(self.config)

            # 执行异步 ping 测试
            is_connected = await service.ping()

            if is_connected:
                logger.info("✅ Redis 连接成功，使用 Redis 缓存")
                self._service_type = "redis"
                return service
            else:
                logger.warning("⚠️ Redis 连接失败，尝试 Memcached...")
                return await self._try_memcached_or_fallback()

        except Exception as e:
            logger.warning(f"⚠️ Redis 初始化失败，尝试 Memcached: {e}")
            return await self._try_memcached_or_fallback()

    async def _try_memcached_or_fallback(self) -> ICacheService:
        """
        尝试连接 Memcached，失败则降级到内存缓存

        策略：
        1. 检查 Memcached 配置完整性
        2. 创建 Memcached 服务并执行 ping 测试
        3. 测试成功：返回 Memcached
        4. 测试失败或配置不完整：降级到内存缓存

        Returns:
            ICacheService: Memcached 或 Memory 服务（已测试可用）
        """
        memcached_config = self.config.memcached

        # 1. 检查配置完整性
        if not memcached_config.host:
            logger.warning("⚠️ Memcached 配置不完整，降级到内存缓存")
            self._service_type = "memory"
            return self._create_memory_service()

        # 2. 创建并测试 Memcached 服务
        try:
            logger.info("🔍 Auto 模式：测试 Memcached 连接...")
            service = MemcachedService(self.config)

            # 执行异步 ping 测试
            is_connected = await service.ping()

            if is_connected:
                logger.info("✅ Memcached 连接成功，使用 Memcached 缓存")
                self._service_type = "memcached"
                return service
            else:
                logger.warning("⚠️ Memcached 连接失败，降级到内存缓存")
                self._service_type = "memory"
                return self._create_memory_service()

        except Exception as e:
            logger.warning(f"⚠️ Memcached 初始化失败，降级到内存缓存: {e}")
            self._service_type = "memory"
            return self._create_memory_service()
