from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from pyspring.core.ioc.interfaces.core import IManaged


# 数据库行数据：字段为任意类型（数据库值），用 dict[str, object] 表达异构键值。
RowData = dict[str, object]


class IDBService(IManaged, ABC):
    """
    数据库服务接口
    """

    @abstractmethod
    async def execute(self, query: str, params: RowData | None = None) -> CursorResult[Any]:
        """执行SQL语句"""
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params: RowData | None = None) -> RowData | None:
        """查询单条记录"""
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params: RowData | None = None) -> list[RowData]:
        """查询多条记录"""
        pass

    @abstractmethod
    async def insert(self, table: str, data: RowData) -> RowData | None:
        """插入数据"""
        pass

    @abstractmethod
    async def engine(self) -> AsyncEngine:
        """
        获取数据库引擎
        """
        pass

    @abstractmethod
    async def session(self) -> AsyncSession:
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
