from __future__ import annotations

import os
from typing import Any

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.log.instance import logger
from pyspring.repositories.db.base_service import BaseAsyncDBService
from pyspring.repositories.db.config import DatabaseConfig
from pyspring.repositories.db.providers.sqlite.interfaces.service import ISqliteService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


@Component
@Singleton
class SqliteService(BaseAsyncDBService, ISqliteService):
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

        # 特殊处理内存数据库
        if self.database != ":memory:":
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

        # 连接池配置 - SQLite 使用 StaticPool，不支持某些参数
        pool_config = sqlite_config.pool
        self._pool_size = pool_config.size
        self._max_overflow = pool_config.max_overflow
        self._pool_recycle = pool_config.recycle
        self._pool_pre_ping = pool_config.pre_ping

        # 延迟初始化
        self._engine: (AsyncEngine) | None = None
        self._session_factory: (async_sessionmaker[AsyncSession]) | None = None

        logger.debug(f"SqliteService initialized for: {self.database}")

    def _ensure_initialized(self):
        """延迟初始化引擎和会话工厂"""
        if self._engine is not None:
            return

        try:
            logger.debug(f"Creating SQLite Engine with url: {self.url}")
            # 获取配置中的echo参数
            sqlite_config = self.config.sqlite
            echo_setting = sqlite_config.pool.echo
            logger.debug(f"SQLite echo setting: {echo_setting}")
            # SQLite 使用 aiosqlite，不支持连接池参数，只支持 echo 参数
            self._engine = create_async_engine(
                self.url,
                echo=echo_setting,
            )
            self._session_factory = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)
            logger.debug(
                f"SQLite connection pool created (pool_size={self._pool_size}, max_overflow={self._max_overflow})"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize SQLite engine: {e}")
            raise e

    def _build_url(self) -> str:
        """构建 SQLite 连接 URL"""
        if self.database == ":memory:":
            return "sqlite+aiosqlite:///:memory:"
        return f"sqlite+aiosqlite:///{self.database}"

    async def insert(self, table: str, data: dict[str, Any]) -> Any:
        """插入数据（SQLite 返回 lastrowid）"""
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            session = await self.session()
            async with session:
                result = await session.execute(text(query), data)
                await session.commit()
                # SQLAlchemy CursorResult 提供 lastrowid；用 getattr 安全获取，避免基类类型推断缺失
                return getattr(result, "lastrowid", None)
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise e
