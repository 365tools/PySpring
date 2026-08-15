from abc import ABC

from pyspring.repositories.cache.service import ICacheService


class IRedisService(ICacheService, ABC):
    """
    Redis缓存服务接口
    """
