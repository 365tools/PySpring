"""
from pyspring.repositories.cache.providers.memory.services.service import MemoryService
from pyspring.repositories.cache.providers.redis.services.service import RedisService

缓存初始化器

在应用启动时初始化缓存服务（Redis/Memory）
"""
import os

from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.log.instance import logger
from pyspring.repositories.base.config.loader import RepositoriesConfigManager
from pyspring.repositories.cache.manager import CacheManagerService
from pyspring.repositories.cache.providers.memory.services.service import MemoryService
from pyspring.repositories.cache.providers.redis.services.service import RedisService


class CacheConnectionInitializer(IStartupInitializer):
    """
    缓存服务初始化器 (CacheConnectionInitializer)
    
    根据配置初始化 Redis 或 Memory 缓存服务
    支持自动降级策略
    """

    def __init__(self, cache_manager: CacheManagerService, enabled: bool = True):
        """
        Args:
            cache_manager: 缓存管理服务实例
            enabled: 是否启用该初始化器
        """
        super().__init__(enabled)
        self.cache_manager = cache_manager
        self.config_manager = RepositoriesConfigManager()

    def get_name(self) -> str:
        return "CacheConnectionInitializer"

    async def initialize(self) -> bool:
        """
        初始化缓存服务
        
        流程:
        1. 读取配置（type, fallback_to_memory）
        2. 根据配置连接对应的缓存服务
        3. 失败时根据降级策略处理
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 1. 读取缓存配置
            cache_config = self.config_manager.get_cache_config()
            cache_type = cache_config.get('type', 'auto').lower()
            fallback_to_memory = cache_config.get('fallback_to_memory', True)

            logger.debug(f"缓存配置: type={cache_type}, fallback={fallback_to_memory}")

            # 2. 根据配置初始化
            if cache_type == 'memory':
                # 强制使用 Memory
                return await self._init_memory()

            elif cache_type == 'redis':
                # 强制使用 Redis
                success = await self._init_redis()
                if not success and fallback_to_memory:
                    logger.warning("Redis 初始化失败，降级到 Memory")
                    return await self._init_memory()
                return success

            else:  # 'auto' 或其他值
                # 优先 Redis，失败时降级到 Memory
                success = await self._init_redis()
                if not success:
                    if fallback_to_memory:
                        logger.info("Redis 不可用，使用 Memory 缓存")
                        return await self._init_memory()
                    else:
                        logger.error("Redis 不可用，且不允许降级到 Memory")
                        return False
                return True

        except Exception as e:
            logger.error(f"缓存初始化异常: {e}", exc_info=True)
            return False

    async def _init_redis(self) -> bool:
        """
        初始化 Redis 缓存
        
        Returns:
            bool: 是否成功
        """
        try:
            # 解析配置
            config_manager = RepositoriesConfigManager()
            cache_config = config_manager.get_cache_config()
            redis_config = cache_config.get('redis', {})

            host = os.getenv('REDIS_HOST', redis_config.get('host', "localhost"))
            port = int(os.getenv('REDIS_PORT', redis_config.get('port', 6379)))
            db = int(os.getenv('REDIS_DB', redis_config.get('db', 0)))
            password = os.getenv('REDIS_PASSWORD', redis_config.get('password', None))
            pool_config = redis_config.get('pool', {})

            # 注入配置
            redis = RedisService(host=host, port=port, db=db, password=password, pool_config=pool_config)
            
            # 测试 Redis 连接
            if await redis.ping():
                self.cache_manager.set_provider(redis)
                logger.info(f"✅ Redis 缓存已连接: {redis.url}")
                return True
            else:
                logger.warning("Redis ping 失败")
                await redis.close()
                return False
        except Exception as e:
            logger.warning(f"Redis 连接失败: {e}")
            return False

    async def _init_memory(self) -> bool:
        """
        初始化 Memory 缓存
        
        Returns:
            bool: 是否成功（Memory 总是成功）
        """
        config_manager = RepositoriesConfigManager()
        cache_config = config_manager.get_cache_config()
        memory_config = cache_config.get('memory', {})

        max_size = memory_config.get('max_size', 1000)
        ttl = memory_config.get('ttl', 3600)

        memory = MemoryService(max_size=max_size, ttl=ttl)
        self.cache_manager.set_provider(memory)
        logger.info(f"✅ Memory 缓存已初始化 (max_size={max_size})")
        return True
