"""
服务接口基类定义
提供统一的服务接口规范，便于依赖注入和动态绑定
"""
from typing import Any, Dict, Protocol, Optional, runtime_checkable

from .IComponent import IComponent


@runtime_checkable
class IService(IComponent, Protocol):
    """
    服务接口协议基类
    
    所有服务都应该实现这个协议，以确保一致的接口
    使用 Protocol 而不是 ABC 以便支持 duck typing
    """

    async def initialize(self) -> bool:
        """
        初始化服务
        
        Returns:
            bool: 初始化是否成功
        """
        ...

    async def destroy(self) -> None:
        """
        销毁服务，释放资源
        """
        ...

    async def get_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息
        
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        ...

    # @abstractmethod
    async def get(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """获取"""
        pass

    # @abstractmethod
    async def list(self, *args: Any, **kwargs: Any) -> Optional[Any] | Any:
        """获取列表"""
        pass

    # @abstractmethod
    async def save(self, *args: Any, **kwargs: Any) -> Optional[Any] | Any:
        """保存"""
        pass

    # @abstractmethod
    async def update(self, *args: Any, **kwargs: Any) -> Optional[Any] | Any:
        """更新"""
        pass

    # @abstractmethod
    async def delete(self, *args: Any, **kwargs: Any) -> Optional[Any] | Any:
        """删除"""
        pass
