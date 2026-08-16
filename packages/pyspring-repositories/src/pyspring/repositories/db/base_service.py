"""
数据库服务公共基类

抽取 postgres / sqlite 等 provider 共有的 CRUD 实现，消除重复代码（DRY）。
子类仅需实现引擎/URL 差异部分（_ensure_initialized / _build_url）与 insert 的方言差异。

解耦说明：
- 本模块只依赖抽象接口 IDBService 与 sqlalchemy，不依赖任何具体 provider。
- 公共逻辑集中在基类，具体 provider 关注点分离，便于新增其他数据库后端。
"""
from __future__ import annotations

import asyncio
from typing import Any, cast, override

from pyspring.core.log.instance import logger
from sqlalchemy import text
from sqlalchemy.engine import CursorResult, Row
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .service import IDBService

# SQLAlchemy 动态行数据：字段为任意类型（数据库值），统一用 dict[str, object] 表达异构键值。
RowData = dict[str, object]


class BaseAsyncDBService(IDBService):
    """
    异步数据库服务公共实现。

    子类需提供：
    - _ensure_initialized(): 延迟初始化 self._engine 与 self._session_factory
    - _build_url() -> str: 构建数据库连接 URL
    - insert(): 方言相关的插入实现（如 RETURNING * / lastrowid）

    提供（默认已实现）：
    - engine / session / execute / fetch_one / fetch_all / update / delete / close / ping
    """

    # 实例属性声明（由子类 __init__ 赋值）
    _engine: AsyncEngine | None
    _session_factory: async_sessionmaker[AsyncSession] | None

    # ---- 由子类实现的抽象/差异部分 ----

    def _ensure_initialized(self) -> None:
        """延迟初始化引擎和会话工厂（子类实现）。"""
        raise NotImplementedError

    def _build_url(self) -> str:
        """构建数据库连接 URL（子类实现）。"""
        raise NotImplementedError

    @override
    async def insert(self, table: str, data: RowData) -> RowData | None:
        """插入数据（子类实现方言差异）。"""
        raise NotImplementedError

    # ---- 公共实现 ----

    @override
    async def engine(self) -> AsyncEngine:
        """获取数据库引擎"""
        self._ensure_initialized()
        if self._engine is None:
            raise RuntimeError(
                f"{type(self).__name__} engine not initialized"
            )
        return self._engine

    @override
    async def session(self) -> AsyncSession:
        """
        获取数据库会话
        """
        self._ensure_initialized()
        if self._session_factory is None:
            raise RuntimeError(
                f"{type(self).__name__} session factory not initialized"
            )
        return self._session_factory()

    @override
    async def execute(self, query: str, params: RowData | None = None) -> CursorResult[Any]:
        """执行SQL语句"""
        try:
            session = await self.session()
            async with session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return cast(CursorResult[Any], result)
        except Exception as e:
            logger.error(f"Execute query failed: {e}")
            raise e

    @override
    async def fetch_one(self, query: str, params: RowData | None = None) -> RowData | None:
        """查询单条记录"""
        try:
            session = await self.session()
            async with session:
                result = await session.execute(text(query), params or {})
                row = result.fetchone()
                if row is None:
                    return None
                return _row_to_dict(row)
        except Exception as e:
            logger.error(f"Fetch one failed: {e}")
            raise e

    @override
    async def fetch_all(self, query: str, params: RowData | None = None) -> list[RowData]:
        """查询多条记录"""
        try:
            session = await self.session()
            async with session:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                return [_row_to_dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Fetch all failed: {e}")
            raise e

    async def update(self, table: str, data: RowData, condition: RowData) -> bool:
        """更新数据"""
        try:
            set_clause = ", ".join([f"{key} = :{key}" for key in data.keys()])
            where_clause = " AND ".join([f"{key} = :where_{key}" for key in condition.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

            # 合并参数
            params: dict[str, object] = {**data}
            params.update({f"where_{key}": value for key, value in condition.items()})

            session = await self.session()
            async with session:
                result = cast(CursorResult[Any], await session.execute(text(query), params))
                await session.commit()
                return int(result.rowcount) > 0
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise e

    async def delete(self, table: str, condition: RowData) -> bool:
        """删除数据"""
        try:
            where_clause = " AND ".join([f"{key} = :{key}" for key in condition.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"

            session = await self.session()
            async with session:
                result = cast(CursorResult[Any], await session.execute(text(query), condition))
                await session.commit()
                return int(result.rowcount) > 0
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise e

    @override
    async def close(self) -> None:
        """关闭数据库连接池，释放所有连接"""
        provider_name = type(self).__name__
        try:
            if self._engine is not None:
                logger.debug(f"Closing {provider_name} connection pool...")
                try:
                    await asyncio.wait_for(
                        self._engine.dispose(close=True),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"{provider_name} connection pool close timeout, forcing cleanup...")
                    # 强制清理
                    self._engine.sync_engine.dispose(close=False)

                self._engine = None
                self._session_factory = None
                logger.debug(f"{provider_name} connection pool released")
        except Exception as e:
            logger.error(f"Failed to close {provider_name} connection pool: {e}")
            # 确保引擎被清空，避免后续访问
            self._engine = None
            self._session_factory = None

    @override
    async def ping(self) -> bool:
        """测试数据库连接是否正常"""
        try:
            session = await self.session()
            async with session:
                _ = await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.warning(f"Ping failed: {e}")
            return False



def _row_to_dict(row: Row[Any]) -> RowData:
    """
    将 SQLAlchemy Row 转为 dict。

    Row._asdict()/mapping 是 SQLAlchemy 提供的 API（返回值类型为动态/受保护），
    相关 Any/私有访问在此用 pyright ignore 压制，避免误报。
    """
    if hasattr(row, "_asdict"):
        return row._asdict()
    return dict(row.mapping)
