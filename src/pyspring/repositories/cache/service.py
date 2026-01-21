"""
缓存服务接口

定义缓存服务的统一接口
"""
from abc import ABC, abstractmethod
from typing import Any

from pyspring.ioc.interfaces.core import IManaged


class ICacheService(IManaged, ABC):
    """缓存服务接口"""

    @abstractmethod
    async def get(self, *args, **kwargs) -> Any:
        """获取缓存"""
        pass

    @abstractmethod
    async def save(self, *args, **kwargs) -> Any:
        """保存缓存"""
        pass

    @abstractmethod
    async def set(self, *args, **kwargs) -> Any:
        """设置缓存"""
        pass

    @abstractmethod
    async def exists(self, *args, **kwargs) -> Any:
        """检查键是否存在"""
        pass

    @abstractmethod
    async def update(self, *args, **kwargs) -> Any:
        """更新缓存"""
        pass

    @abstractmethod
    async def delete(self, *args, **kwargs) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""

    @abstractmethod
    async def ping(self) -> bool:
        """检查服务可用性"""
