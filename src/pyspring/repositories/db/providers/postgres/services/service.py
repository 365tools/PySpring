import asyncio
from typing import Any, Optional, List, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine

from pyspring.log.instance import logger
from ..interfaces.service import IPostgresService


class PostgresService(IPostgresService):
    """PostgreSQL数据库服务实现"""

    def __init__(self, host: str = "localhost", port: int = 5432, database: str = "postgres",
                 user: str = "postgres", password: Optional[str] = None, pool_config: Optional[dict] = None):
        """
        初始化 Postgres 服务 (纯粹的参数注入，不依赖配置管理器)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool_config = pool_config or {}

        self.url = self._build_url()

        # 从配置中获取连接池参数
        self._pool_size = self.pool_config.get('size', 5)
        self._max_overflow = self.pool_config.get('max_overflow', 10)
        self._pool_recycle = self.pool_config.get('recycle', 3600)
        self._pool_timeout = self.pool_config.get('timeout', 30)
        self._pool_pre_ping = self.pool_config.get('pre_ping', True)

        # 延迟初始化
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None

    def _ensure_initialized(self):
        """延迟初始化引擎和会话工厂"""
        if self._engine is not None:
            return

        try:
            logger.debug(f"🔧 Creating Postgres Engine with url: {self._mask_password(self.url)}")
            self._engine = create_async_engine(
                self.url,
                echo=False,
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
            logger.debug(f"🔗 PostgreSQL 连接池已创建 (pool_size={self._pool_size}, max_overflow={self._max_overflow})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Postgres engine (check asyncpg installation): {e}")
            raise e

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

    async def engine(self):
        """获取数据库引擎"""
        self._ensure_initialized()
        return self._engine

    async def session(self) -> AsyncSession:
        """
        获取数据库会话
        """
        self._ensure_initialized()
        if self._session_factory:
            return self._session_factory()
        raise RuntimeError("Postgres session factory not initialized")

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行SQL语句"""
        try:
            async with await self.session() as session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
        except Exception as e:
            logger.error(f"🚨 Execute query failed: {e}")
            raise e

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """查询单条记录"""
        try:
            async with await self.session() as session:
                result = await session.execute(text(query), params or {})
                row = result.fetchone()
                if row is None:
                    return None
                return dict(row._mapping)
        except Exception as e:
            logger.error(f"🚨 Fetch one failed: {e}")
            raise e

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """查询多条记录"""
        try:
            async with await self.session() as session:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"🚨 Fetch all failed: {e}")
            raise e

    async def insert(self, table: str, data: Dict[str, Any]) -> Any:
        """插入数据"""
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *"

            async with await self.session() as session:
                result = await session.execute(text(query), data)
                await session.commit()
                row = result.fetchone()
                return dict(row._mapping) if row else None
        except Exception as e:
            logger.error(f"🚨 Insert failed: {e}")
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

            async with await self.session() as session:
                result = await session.execute(text(query), params)
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"🚨 Update failed: {e}")
            raise e

    async def delete(self, table: str, condition: Dict[str, Any]) -> bool:
        """删除数据"""
        try:
            where_clause = " AND ".join([f"{key} = :{key}" for key in condition.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"

            async with await self.session() as session:
                result = await session.execute(text(query), condition)
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"🚨 Delete failed: {e}")
            raise e

    async def close(self) -> None:
        """关闭数据库连接池，释放所有连接"""
        try:
            if self._engine is not None:
                # ✅ 使用 asyncio.wait_for 添加超时保护
                logger.debug("🔄 正在关闭 PostgreSQL 连接池...")
                try:
                    await asyncio.wait_for(
                        self._engine.dispose(close=True),
                        timeout=5.0  # 5秒超时
                    )
                except asyncio.TimeoutError:
                    logger.warning("⚠️  PostgreSQL 连接池关闭超时，强制清理...")
                    # 强制清理
                    self._engine.sync_engine.dispose(close=False)

                self._engine = None
                self._session_factory = None
                logger.debug("🔌 PostgreSQL 连接池已释放")
        except Exception as e:
            logger.error(f"🚨 关闭 PostgreSQL 连接池失败: {e}")
            # 确保引擎被清空，避免后续访问
            self._engine = None
            self._session_factory = None

    async def ping(self) -> bool:
        """
        测试数据库连接是否正常
        """
        try:
            async with await self.session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.warning(f"❌ Ping postgresql failed: {e}")
            return False
