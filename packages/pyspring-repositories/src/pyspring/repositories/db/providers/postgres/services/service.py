from __future__ import annotations

from typing import override

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.log.instance import logger
from pyspring.repositories.db.base_service import BaseAsyncDBService, RowData
from pyspring.repositories.db.providers.postgres.interfaces.service import IPostgresService
from pyspring.repositories.db.config import DatabaseConfig


@Component
@Singleton
class PostgresService(BaseAsyncDBService, IPostgresService):
    """PostgreSQL数据库服务实现（由 IOC 容器管理）"""

    # 实例属性注解（由 __init__ 赋值）
    config: DatabaseConfig
    host: str
    port: int
    database: str
    user: str | None
    password: str | None
    url: str
    _pool_size: int
    _max_overflow: int
    _pool_recycle: int
    _pool_timeout: int
    _pool_pre_ping: bool

    def __init__(self, database_config: DatabaseConfig):
        """
        通过 IOC 注入配置

        Args:
            database_config: DatabaseConfig 实例（自动注入）
        """
        self.config = database_config

        postgres_config = self.config.postgresql
        self.host = postgres_config.host
        self.port = postgres_config.port
        self.database = postgres_config.database
        self.user = postgres_config.user
        self.password = postgres_config.password
        self.url = self._build_url()

        # 连接池配置
        pool_config = postgres_config.pool
        self._pool_size = pool_config.size
        self._max_overflow = pool_config.max_overflow
        self._pool_recycle = pool_config.recycle
        self._pool_timeout = pool_config.timeout
        self._pool_pre_ping = pool_config.pre_ping

        # 延迟初始化
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

        logger.debug(f"PostgresService initialized for {self.host}:{self.port}/{self.database}")

    @override
    def _ensure_initialized(self) -> None:
        """延迟初始化引擎和会话工厂"""
        if self._engine is not None:
            return

        try:
            logger.debug(f"Creating Postgres Engine with url: {self._mask_password(self.url)}")
            # 获取配置中的echo参数
            postgres_config = self.config.postgresql
            echo_setting = postgres_config.pool.echo
            logger.debug(f"PostgreSQL echo setting: {echo_setting}")
            self._engine = create_async_engine(
                self.url,
                echo=echo_setting,
                pool_size=self._pool_size,
                max_overflow=self._max_overflow,
                pool_recycle=self._pool_recycle,
                pool_timeout=self._pool_timeout,
                pool_pre_ping=self._pool_pre_ping,
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.debug(f"PostgreSQL connection pool created (pool_size={self._pool_size}, max_overflow={self._max_overflow})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Postgres engine (check asyncpg installation): {e}")
            raise e

    @override
    def _build_url(self) -> str:
        """构建 PostgreSQL 连接 URL"""
        if self.password:
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql+asyncpg://{self.user}@{self.host}:{self.port}/{self.database}"

    def _mask_password(self, url: str) -> str:
        """隐藏URL中的密码"""
        if self.password and self.password in url:
            return url.replace(self.password, "****")
        return url

    @override
    async def insert(self, table: str, data: RowData) -> RowData | None:
        """插入数据（PostgreSQL 支持 RETURNING * 返回整行）"""
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *"

            session = await self.session()
            async with session:
                result = await session.execute(text(query), data)
                await session.commit()
                row = result.fetchone()
                if row is None:
                    return None
                if hasattr(row, "_asdict"):
                    return row._asdict()
                return dict(row.mapping)
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise e

    @override
    async def ping(self) -> bool:
        """测试数据库连接是否正常"""
        try:
            session = await self.session()
            async with session:
                _ = await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.warning(f"Ping postgresql failed: {e}")
            return False
