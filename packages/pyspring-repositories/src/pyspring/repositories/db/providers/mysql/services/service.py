'''
MySQL 数据库服务实现
'''
from typing import Any, cast

from pyspring.core.log.instance import logger
from sqlalchemy import text
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import QueuePool

from ....service import IDBService


class MysqlService(IDBService):
    '''MySQL 数据库服务实现'''

    def __init__(self, config):
        '''
        初始化 MySQL 服务
        
        Args:
            config: 数据库配置对象
        '''
        self.config = config
        self._engine: (AsyncEngine) | None = None
        self._connected = False

        try:
            mysql_config = getattr(config, 'mysql', None)

            # 初始化连接池配置
            if mysql_config:
                pool_config = mysql_config.pool
                self._pool_size = pool_config.size
                self._max_overflow = pool_config.max_overflow
                self._pool_recycle = pool_config.pool_recycle
                self._pool_timeout = pool_config.pool_timeout
                self._pool_pre_ping = pool_config.pool_pre_ping
                self._echo = pool_config.echo
            else:
                # 默认配置
                self._pool_size = 5
                self._max_overflow = 10
                self._pool_recycle = 3600
                self._pool_timeout = 30
                self._pool_pre_ping = True
                self._echo = False
            if mysql_config:
                # 构建连接字符串
                user = mysql_config.user or ""
                password = f":{mysql_config.password}" if mysql_config.password else ""
                auth_part = f"{user}{password}@" if user else ""

                # 构建连接字符串，包含连接池参数
                connection_string = (
                    f"mysql+asyncmy://{auth_part}{mysql_config.host}:{mysql_config.port}/"
                    f"{mysql_config.database}?charset={mysql_config.charset}"
                )

                # 从配置中获取连接池参数
                pool_config = mysql_config.pool

                self._engine = create_async_engine(
                    connection_string,
                    poolclass=QueuePool,
                    pool_size=pool_config.size,
                    max_overflow=pool_config.max_overflow,
                    pool_recycle=pool_config.pool_recycle,
                    pool_pre_ping=pool_config.pool_pre_ping,
                    pool_timeout=pool_config.pool_timeout,
                    echo=pool_config.echo
                )

            logger.info("✅ MySQL 服务初始化完成")
            self._connected = True

        except ImportError as e:
            logger.error(f"❌ MySQL 驱动未安装，无法使用 MySQL 服务: {e}")
            self._connected = False
        except Exception as e:
            logger.error(f"❌ MySQL 服务初始化失败: {e}")
            self._connected = False

    async def ping(self) -> bool:
        '''
        检查 MySQL 连接状态
        
        Returns:
            bool: 连接是否正常
        '''
        if not self._connected or not self._engine:
            return False

        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"MySQL ping 测试失败: {e}")
            return False

    async def execute(self, query: str, params: (dict[str, Any]) | None = None) -> Any:
        '''
        执行查询
        
        Args:
            query: SQL 查询语句
            params: 查询参数
            
        Returns:
            Any: 查询结果
        '''
        if not self._engine:
            raise RuntimeError("MySQL 服务未初始化")

        try:
            async with AsyncSession(self._engine) as session:
                async with session.begin():
                    result = await session.execute(text(query), params or {})
                    await session.commit()
                    return result
        except Exception as e:
            logger.error(f"[MySQL] Execute 失败: {e}")
            raise

    async def fetch_one(self, query: str, params: (dict[str, Any]) | None = None) -> (dict[str, Any]) | None:
        '''
        获取单条记录
        
        Args:
            query: SQL 查询语句
            params: 查询参数
            
        Returns:
            (dict[str, Any]) | None: 单条记录，不存在则返回 None
        '''
        if not self._engine:
            raise RuntimeError("MySQL 服务未初始化")

        try:
            async with AsyncSession(self._engine) as session:
                result = await session.execute(text(query), params or {})
                row = result.fetchone()
                if row:
                    return dict(row._mapping)
                return None
        except Exception as e:
            logger.error(f"[MySQL] Fetch one 失败: {e}")
            raise

    async def fetch_all(self, query: str, params: (dict[str, Any]) | None = None) -> list[dict[str, Any]]:
        '''
        获取多条记录
        
        Args:
            query: SQL 查询语句
            params: 查询参数
            
        Returns:
            list[dict[str, Any]]: 记录列表
        '''
        if not self._engine:
            raise RuntimeError("MySQL 服务未初始化")

        try:
            async with AsyncSession(self._engine) as session:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            logger.error(f"[MySQL] Fetch all 失败: {e}")
            raise

    async def close(self) -> None:
        '''关闭连接'''
        if self._engine:
            await self._engine.dispose()
            self._connected = False
            logger.info("[MySQL] 连接已关闭")

    async def engine(self):
        '''获取数据库引擎'''
        if not self._engine:
            raise RuntimeError("MySQL 服务未初始化")
        return self._engine

    async def session(self):
        '''获取数据库会话'''
        if not self._engine:
            raise RuntimeError("MySQL 服务未初始化")
        from sqlalchemy.ext.asyncio import async_sessionmaker
        session_factory = async_sessionmaker(
            self._engine,
            expire_on_commit=False
        )
        return session_factory()

    async def insert(self, table: str, data: dict[str, Any]) -> Any:
        '''插入数据'''
        from sqlalchemy import text
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            async with AsyncSession(self._engine) as session:
                async with session.begin():
                    result = await session.execute(text(query), data)
                    await session.commit()
                    return cast(CursorResult[Any], result).lastrowid
        except Exception as e:
            logger.error(f"[MySQL] Insert 失败: {e}")
            raise e
