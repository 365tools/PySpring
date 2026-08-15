from abc import ABC

from pyspring.repositories.cache.service import ICacheService


class IMemoryService(ICacheService, ABC):
    """
    内存缓存服务接口
    """
