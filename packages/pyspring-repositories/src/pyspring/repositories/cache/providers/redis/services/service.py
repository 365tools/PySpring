"""
Redis 缓存服务实现
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import redis.asyncio as redis
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.log.instance import logger
from redis.asyncio.connection import ConnectionPool

from ....config import CacheConfig
from ..interfaces.service import IRedisService


@Component
@Singleton
class RedisService(IRedisService):
    """Redis 缓存服务（由 IOC 容器管理）"""

    def __init__(self, cache_config: CacheConfig):
        """
        通过 IOC 注入配置
        
        Args:
            cache_config: CacheConfig 实例（自动注入）
        """
        self.config: CacheConfig = cache_config

        # Redis 配置
        redis_config = self.config.redis
        self.host = redis_config.host
        self.port = redis_config.port
        self.db = redis_config.db
        self.password = redis_config.password
        self.url = self._build_url()

        # 连接池配置
        pool_config = redis_config.pool
        self.max_connections = pool_config.max_connections
        self.socket_keepalive = pool_config.socket_keepalive
        self.socket_connect_timeout = pool_config.socket_connect_timeout
        self.retry_on_timeout = pool_config.retry_on_timeout

        # 创建连接池（轻量级，不建立实际连接）
        self._connection_pool: ConnectionPool = ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            encoding="utf-8",
            decode_responses=True,
            max_connections=self.max_connections,
            socket_keepalive=self.socket_keepalive,
            socket_connect_timeout=self.socket_connect_timeout,
            retry_on_timeout=self.retry_on_timeout
        )
        self._redis_client: redis.Redis = redis.Redis(connection_pool=self._connection_pool)

        logger.debug(f"RedisService initialized for {self.host}:{self.port} (max_connections={self.max_connections})")

    def _build_url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        else:
            return f"redis://{self.host}:{self.port}/{self.db}"

    def _mask_password(self, url: str) -> str:
        if self.password and self.password in url:
            return url.replace(self.password, "****")
        return url

    async def get(self, key: str) -> (Any) | None:
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

    async def list(self, key: str) -> (Any) | None:
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

    async def save(self, key: str, value: Any, ttl: (int) | None = None) -> Any:
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            result = await self._redis_client.set(key, serialized_value, ex=ttl)
            return result is True
        except Exception as e:
            raise e

    async def set(self, key: str, value: Any, ex: (int) | None = None) -> bool:
        """设置缓存，支持过期时间"""
        return await self.save(key, value, ttl=ex)

    async def exists(self, key: str) -> bool:
        try:
            result = await self._redis_client.exists(key)
            return result > 0
        except Exception as e:
            raise e

    async def update(self, key: str, value: Any, ttl: (int) | None = None) -> Any:
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
            # redis-py 存根将 ping() 误标为同步 bool，但运行时为协程（已实测）
            return await self._redis_client.ping()  # pyright: ignore[reportGeneralTypeIssues]
        except Exception as e:
            raise e

    async def close(self) -> None:
        """关闭 Redis 连接池，释放所有连接"""
        try:
            try:
                await asyncio.wait_for(
                    self._redis_client.aclose(),
                    timeout=3.0
                )
            except asyncio.TimeoutError:
                logger.warning("Redis 客户端关闭超时")
            except Exception as e:
                logger.warning(f"Redis 客户端关闭异常: {e}")

            try:
                await asyncio.wait_for(
                    self._connection_pool.disconnect(),
                    timeout=3.0
                )
            except asyncio.TimeoutError:
                logger.warning("Redis 连接池断开超时，强制关闭")
                try:
                    await self._connection_pool.disconnect(inuse_connections=True)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Redis 连接池断开异常: {e}")
            logger.debug("Redis connection pool released")
        except Exception as e:
            logger.error(f"关闭 Redis 连接失败: {e}")
