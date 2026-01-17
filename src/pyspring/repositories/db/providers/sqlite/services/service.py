import asyncio
import os
from typing import Any, Optional, List, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from pyspring.log.instance import logger
from pyspring.utils.config.finder import detect_project_root
from ..interfaces.service import ISqliteService


class SqliteService(ISqliteService):
    """SQLite数据库服务实现"""

    def __init__(self, database: str = "data/app.db", resolve_path: bool = True, pool_config: Optional[dict] = None):
        self.database = database
        self.pool_config = pool_config or {}

        # 如果是相对路径, 基于项目根目录解析
        if resolve_path and not os.path.isabs(self.database):
            try:
                project_root = detect_project_root()
                self.database = str(project_root / self.database)
            except Exception:
                # Fallback if detection fails (e.g. in tests without project structure)
                pass

        # 确保数据库目录存在
        db_dir = os.path.dirname(self.database)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.url = self._build_url()

        # 从配置中获取连接池参数
        pool_size = self.pool_config.get('size', 5)
        max_overflow = self.pool_config.get('max_overflow', 10)
        pool_recycle = self.pool_config.get('recycle', 3600)

        # 直接在构造函数中创建连接池
        self._engine = create_async_engine(
            self.url,
            echo=False,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        logger.debug(f"🔧 SqliteService init with url: {self.url}")
        logger.debug(f"🔗 SQLite 连接池已创建 (pool_size={pool_size}, max_overflow={max_overflow})")

    def _build_url(self) -> str:
        """构建 SQLite 连接 URL"""
        return f"sqlite+aiosqlite:///{self.database}"

    async def get_engine(self):
        """获取数据库引擎(已在 __init__ 中创建)"""
        return self._engine

    async def get_session(self) -> AsyncSession:
        """
        获取数据库会话
        """
        return self._session_factory()

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行SQL语句"""
        try:
            async with await self.get_session() as session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
        except Exception as e:
            logger.error(f"🚨 Execute query failed: {e}")
            raise e

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """查询单条记录"""
        try:
            async with await self.get_session() as session:
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
            async with await self.get_session() as session:
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
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            async with await self.get_session() as session:
                result = await session.execute(text(query), data)
                await session.commit()
                # SQLite 使用 last_insert_rowid
                return result.lastrowid
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

            async with await self.get_session() as session:
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

            async with await self.get_session() as session:
                result = await session.execute(text(query), condition)
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"🚨 Delete failed: {e}")
            raise e

    async def close(self) -> None:
        """关闭数据库连接池, 释放所有连接"""
        try:
            if self._engine is not None:
                # ✅ 使用 asyncio.wait_for 添加超时保护
                logger.debug("🔄 正在关闭 SQLite 连接池...")
                try:
                    await asyncio.wait_for(
                        self._engine.dispose(close=True),
                        timeout=5.0  # 5秒超时
                    )
                except asyncio.TimeoutError:
                    logger.warning("⚠️  SQLite 连接池关闭超时，强制清理...")
                    # 强制清理
                    self._engine.sync_engine.dispose(close=False)

                self._engine = None
                self._session_factory = None
                logger.debug("🔌 SQLite 连接池已释放")
        except Exception as e:
            logger.error(f"🚨 关闭 SQLite 连接池失败: {e}")
            # 确保引擎被清空，避免后续访问
            self._engine = None
            self._session_factory = None

    async def ping(self) -> bool:
        """
        测试数据库连接是否正常
        """
        try:
            async with await self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.warning(f"🚨 Ping failed: {e}")
            return False
