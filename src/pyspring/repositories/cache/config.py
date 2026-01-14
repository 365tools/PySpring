"""
缓存配置 - Infrastructure层

通用的缓存配置类，支持多种缓存类型
可在不同项目中复用
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from pyspring.core.configuration.base import ConfigSection


class RedisPoolConfig(ConfigSection):
    """Redis连接池配置"""
    max_connections: int = Field(default=50, description="最大连接数")
    socket_keepalive: bool = Field(default=True, description="保持连接")
    socket_connect_timeout: int = Field(default=5, description="连接超时(秒)")
    retry_on_timeout: bool = Field(default=True, description="超时重试")


class RedisConfig(ConfigSection):
    """Redis配置"""
    model_config = SettingsConfigDict(populate_by_name=True, extra='ignore')

    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=6379, ge=1, le=65535, description="端口号")
    db: int = Field(default=0, ge=0, description="数据库编号")
    password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD", description="密码")
    pool: RedisPoolConfig = Field(default_factory=RedisPoolConfig, description="连接池配置")


class MemcachedConfig(ConfigSection):
    """Memcached配置"""
    servers: list[str] = Field(default=["localhost:11211"], description="服务器列表")
    max_connections: int = Field(default=10, description="最大连接数")


class MemoryConfig(ConfigSection):
    """内存缓存配置"""
    max_size: int = Field(default=1000, description="最大缓存项数")
    ttl: int = Field(default=3600, description="默认过期时间(秒)")


class CacheConfig(ConfigSection):
    """通用缓存配置"""
    type: str = Field(default="memory", description="缓存类型：redis、memcached、memory")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis配置")
    memcached: MemcachedConfig = Field(default_factory=MemcachedConfig, description="Memcached配置")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="内存缓存配置")


# 向后兼容：为旧代码提供别名
class RedisConfig_Alias(RedisConfig):
    """Redis配置别名(向后兼容)"""
    pass


__all__ = [
    "RedisPoolConfig",
    "RedisConfig",
    "MemcachedConfig",
    "MemoryConfig",
    "CacheConfig",
]
