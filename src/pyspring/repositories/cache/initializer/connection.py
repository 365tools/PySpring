"""
缓存初始化器

在应用启动时初始化缓存服务（Redis/Memory）
"""
from pyspring.core.interfaces.IStartupInitializer import IStartupInitializer
from pyspring.log.instance import logger
from pyspring.repositories.cache.manager import CacheManagerService
from pyspring.repositories.base.config.loader import RepositoriesConfigManager


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
            from pyspring.repositories.cache.ins.redis.impl.service import RedisService
            redis = RedisService()
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
        from pyspring.repositories.cache.ins.memory.impl.service import MemoryService
        memory = MemoryService()
        self.cache_manager.set_provider(memory)
        logger.info("✅ Memory 缓存已初始化")
        return True
