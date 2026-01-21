from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict

from pyspring.ioc.interfaces.core import IManaged


class IDBService(IManaged, ABC):
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

    @abstractmethod
    async def engine(self) -> Any:
        """
        获取数据库引擎
        """
        pass

    @abstractmethod
    async def session(self) -> Any:
        """
        获取数据库会话
        """
        pass

    async def close(self) -> None:
        """
        关闭数据库服务
        """
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """
        测试数据库服务是否正常
        """
        pass