from abc import ABC, abstractmethod
from pyspring.interfaces.ISingleton import ISingletonService
from typing import Any, Optional, List, Dict


class IDBService(ISingletonService, ABC):
    """
    数据库服务接口
    """

    @abstractmethod
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行SQL语句"""
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """查询单条记录"""
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """查询多条记录"""
        pass

    @abstractmethod
    async def insert(self, table: str, data: Dict[str, Any]) -> Any:
        """插入数据"""
        pass

    # @abstractmethod
    # async def update(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    #     """更新数据"""
    #     pass
    #
    # @abstractmethod
    # async def delete(self, table: str, condition: Dict[str, Any]) -> bool:
    #     """删除数据"""
    #     pass

    @staticmethod
    async def get_engine(self):
        """
        获取数据库引擎
        """
        pass

    @abstractmethod
    async def get_session(self) -> Any:
        """
        获取数据库会话
        """
        pass

    async def close(self) -> None:
        """
        关闭数据库服务
        """

    @abstractmethod
    async def ping(self) -> bool:
        """
        测试数据库服务是否正常
        """
        pass
