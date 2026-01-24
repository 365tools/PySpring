from __future__ import annotations

import asyncio
import os
from typing import Any, Optional, List, Dict

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.log.instance import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine

from ..interfaces.service import ISqliteService
from ....config import DatabaseConfig


@Component()
@Singleton
class SqliteService(ISqliteService):
    """SQLite数据库服务实现（由 IOC 容器管理）"""

    def __init__(self, database_config: DatabaseConfig):
        """
        通过 IOC 注入配置
        
        Args:
            database_config: DatabaseConfig 实例（自动注入）
        """
        self.config: DatabaseConfig = database_config

        sqlite_config = self.config.sqlite
        self.database = sqlite_config.database

        # 如果是相对路径，基于当前工作目录解析（用户项目根目录）
        if not os.path.isabs(self.database):
            # 优先使用当前工作目录（用户项目），而不是框架安装目录
            cwd = os.getcwd()
            self.database = os.path.join(cwd, self.database)

        # 确保数据库目录存在
        db_dir = os.path.dirname(self.database)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.url = self._build_url()

        # 连接池配置
        pool_config = sqlite_config.pool
        self._pool_size = pool_config.size
        self._max_overflow = pool_config.max_overflow
        self._pool_recycle = pool_config.recycle

        # 延迟初始化
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None

        logger.debug(f"SqliteService initialized for: {self.database}")

    def _ensure_initialized(self):
        """延迟初始化引擎和会话工厂"""
        if self._engine is not None:
            return

        try:
            logger.debug(f"Creating SQLite Engine with url: {self.url}")
            self._engine = create_async_engine(
                self.url,
                echo=False,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_recycle=self._pool_recycle,
                pool_pre_ping=True,
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.debug(f"SQLite connection pool created (pool_size={self._pool_size}, max_overflow={self._max_overflow})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SQLite engine: {e}")
            raise e

    def _build_url(self) -> str:
        """构建 SQLite 连接 URL"""
        return f"sqlite+aiosqlite:///{self.database}"

    async def engine(self):
        """获取数据库引擎"""
        self._ensure_initialized()
        return self._engine

    async def session(self) -> AsyncSession:
        """
        获取数据库会话
        """
        self._ensure_initialized()
        return self._session_factory()

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行SQL语句"""
        try:
            session = await self.session()
            async with session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
        except Exception as e:
            logger.error(f"Execute query failed: {e}")
            raise e

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """查询单条记录"""
        try:
            session = await self.session()
            async with session:
                result = await session.execute(text(query), params or {})
                row = result.fetchone()
                if row is None:
                    return None
                return row._asdict() if hasattr(row, '_asdict') else dict(row._mapping)
        except Exception as e:
            logger.error(f"Fetch one failed: {e}")
            raise e

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """查询多条记录"""
        try:
            session = await self.session()
            async with session:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                return [row._asdict() if hasattr(row, '_asdict') else dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"Fetch all failed: {e}")
            raise e

    async def insert(self, table: str, data: Dict[str, Any]) -> Any:
        """插入数据"""
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            session = await self.session()
            async with session:
                result = await session.execute(text(query), data)
                await session.commit()
                return result.lastrowid
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise e

    async def update(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """更新数据"""
        try:
            set_clause = ", ".join([f"{key} = :{key}" for key in data.keys()])
            where_clause = " AND ".join([f"{key} = :where_{key}" for key in condition.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

            # 合并参数
            params = {**data}
            params.update({f"where_{key}": value for key, value in condition.items()})

            session = await self.session()
            async with session:
                result = await session.execute(text(query), params)
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise e

    async def delete(self, table: str, condition: Dict[str, Any]) -> bool:
        """删除数据"""
        try:
            where_clause = " AND ".join([f"{key} = :{key}" for key in condition.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"

            session = await self.session()
            async with session:
                result = await session.execute(text(query), condition)
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise e

    async def close(self) -> None:
        """关闭数据库连接池, 释放所有连接"""
        try:
            if self._engine is not None:
                # ✅ 使用 asyncio.wait_for 添加超时保护
                logger.debug("Closing SQLite connection pool...")
                try:
                    await asyncio.wait_for(
                        self._engine.dispose(close=True),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("SQLite connection pool close timeout, forcing cleanup...")
                    # 强制清理
                    self._engine.sync_engine.dispose(close=False)

                self._engine = None
                self._session_factory = None
                logger.debug("SQLite connection pool released")
        except Exception as e:
            logger.error(f"Failed to close SQLite connection pool: {e}")
            # 确保引擎被清空，避免后续访问
            self._engine = None
            self._session_factory = None

    async def ping(self) -> bool:
        """
        测试数据库连接是否正常
        """
        try:
            session = await self.session()
            async with session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.warning(f"Ping failed: {e}")
            return False
