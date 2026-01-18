import asyncio
import json
from typing import Optional, Any

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from pyspring.log.instance import logger
from ..interfaces.service import IRedisService


class RedisService(IRedisService):

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None, pool_config: Optional[dict] = None):
        """
        初始化 Redis 服务
        
        Args:
            host: Redis 主机地址
            port: Redis 端口
            db: 数据库索引
            password: 密码
            pool_config: 连接池配置
        """
        # 直接使用传入参数，配置加载逻辑外移到 Initializer
        # 支持环境变量覆盖（保留环境变量逻辑作为最后的防线，或者也应该外移？
        # 为了彻底纯粹，环境变量也应该在外层处理。但保留在此处作为默认值解析逻辑也可以。
        # 建议：这里只做纯赋值。外层 Initializer 负责解析所有配置来源。

        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.pool_config = pool_config or {}

        self.url = self._build_url()

        # 从配置中获取连接池参数
        max_connections = self.pool_config.get('max_connections', 50)
        socket_keepalive = self.pool_config.get('socket_keepalive', True)
        socket_connect_timeout = self.pool_config.get('socket_connect_timeout', 5)
        retry_on_timeout = self.pool_config.get('retry_on_timeout', True)

        # 直接在构造函数中创建连接池和客户端
        self._connection_pool: Optional[ConnectionPool] = ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            encoding="utf-8",
            decode_responses=True,
            max_connections=max_connections,
            socket_keepalive=socket_keepalive,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout
        )
        self._redis_client: Optional[redis.Redis] = redis.Redis(connection_pool=self._connection_pool)

        logger.debug(f"🔧 RedisService init with url: {self._mask_password(self.url)}")
        logger.debug(f"🔗 Redis 连接池已创建 (max_connections={max_connections})")

    def _build_url(self) -> str:
        """
        构建 Redis 连接 URL。
        如果提供了密码，则将其包含在 URL 中。
        """
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        else:
            return f"redis://{self.host}:{self.port}/{self.db}"

    def _mask_password(self, url: str) -> str:
        """隐藏URL中的密码"""
        if self.password and self.password in url:
            return url.replace(self.password, "****")
        return url

    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self._redis_client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            raise e

    async def list(self, key: str) -> Optional[Any]:
        try:
            value = await self._redis_client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            raise e

    async def save(self, key: str, value: Any, ttl: Optional[int] = None) -> Any:
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            result = await self._redis_client.set(key, serialized_value, ex=ttl)
            return result is True
        except Exception as e:
            raise e

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置缓存（支持过期时间），兼容 Redis 原生 API"""
        return await self.save(key, value, ttl=ex)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            result = await self._redis_client.exists(key)
            return result > 0
        except Exception as e:
            raise e

    async def update(self, key: str, value: Any, ttl: Optional[int] = None) -> Any:
        return await self.save(key, value, ttl)

    async def delete(self, key: str) -> bool:
        try:
            result = await self._redis_client.delete(key)
            return result > 0
        except Exception as e:
            raise e

    async def clear(self) -> None:
        try:
            await self._redis_client.flushdb()
        except Exception as e:
            raise e

    async def ping(self) -> bool:
        try:
            return await self._redis_client.ping()
        except Exception as e:
            raise e

    async def close(self) -> None:
        """关闭 Redis 连接池，释放所有连接"""
        try:
            # ✅ 先关闭客户端，再关闭连接池
            if self._redis_client is not None:
                try:
                    await asyncio.wait_for(
                        self._redis_client.aclose(),
                        timeout=3.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("⚠️  Redis 客户端关闭超时")
                except Exception as e:
                    logger.warning(f"⚠️  Redis 客户端关闭异常: {e}")
                finally:
                    self._redis_client = None

            if self._connection_pool is not None:
                try:
                    await asyncio.wait_for(
                        self._connection_pool.disconnect(),
                        timeout=3.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("⚠️  Redis 连接池断开超时，强制关闭...")
                    # ✅ 强制关闭所有连接
                    try:
                        await self._connection_pool.disconnect(inuse_connections=True)
                    except:
                        pass
                except Exception as e:
                    logger.warning(f"⚠️  Redis 连接池断开异常: {e}")
                finally:
                    self._connection_pool = None
                    logger.debug("🔌 Redis 连接池已释放")
        except Exception as e:
            logger.error(f"🚨 关闭 Redis 连接失败: {e}")
            # 确保资源被清空
            self._redis_client = None
            self._connection_pool = None
