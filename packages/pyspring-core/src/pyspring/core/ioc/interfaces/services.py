"""
业务服务接口（可选）

这些接口仅供特定类型的服务使用，不是所有服务都需要实现。
"""
from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class ICrudService(Protocol):
    """
    CRUD服务接口
    
    仅用于需要标准CRUD操作的数据访问服务。
    不是所有服务都需要实现此接口。
    
    适用场景：
    - Repository层服务
    - 数据访问层服务
    - 需要标准化CRUD操作的服务
    
    不适用场景：
    - 业务逻辑服务
    - 工具类服务
    - 管理器服务
    """

    async def get(self, *args: Any, **kwargs: Any) -> (Any) | None:
        """获取单个实体"""
        ...

    async def list(self, *args: Any, **kwargs: Any) -> list[Any]:
        """获取实体列表"""
        ...

    async def save(self, *args: Any, **kwargs: Any) -> Any:
        """保存实体"""
        ...

    async def update(self, *args: Any, **kwargs: Any) -> Any:
        """更新实体"""
        ...

    async def delete(self, *args: Any, **kwargs: Any) -> bool:
        """删除实体"""
        ...


@runtime_checkable
class IRepository(ICrudService, Protocol):
    """
    Repository接口
    
    继承CRUD接口，表示这是一个数据仓储服务。
    可以添加额外的查询方法。
    """
    pass


__all__ = ['ICrudService', 'IRepository']
