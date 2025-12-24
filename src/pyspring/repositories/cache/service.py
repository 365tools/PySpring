from abc import ABC, abstractmethod
from pyspring.interfaces.ISingleton import ISingletonService
from typing import Any


class ICacheService(ISingletonService, ABC):
    """
    缓存服务接口
    """

    @abstractmethod
    async def get(self, *args, **kwargs) -> Any:
        """获取缓存数据"""
        pass

    @abstractmethod
    async def save(self, *args, **kwargs) -> Any:
        """保存缓存数据"""
        pass

    @abstractmethod
    async def set(self, *args, **kwargs) -> Any:
        """设置缓存（支持过期时间）"""
        pass

    @abstractmethod
    async def exists(self, *args, **kwargs) -> Any:
        """检查键是否存在"""
        pass

    @abstractmethod
    async def update(self, *args, **kwargs) -> Any:
        """更新缓存数据"""
        pass

    @abstractmethod
    async def delete(self, *args, **kwargs) -> bool:
        """删除缓存数据"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """
        清空缓存
        """

    @abstractmethod
    async def ping(self) -> bool:
        """
        测试缓存服务是否正常
        """
