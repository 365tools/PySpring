"""
缓存配置

支持 Redis 和内存缓存的配置管理
"""

from typing import ClassVar

from pydantic import Field
from pydantic_settings import SettingsConfigDict
from pyspring.core.abstracts.config import ConfigSection
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton


class RedisPoolConfig(ConfigSection):
    """Redis连接池配置"""

    max_connections: int = Field(default=50, description="最大连接数")
    socket_keepalive: bool = Field(default=True, description="保持连接")
    socket_connect_timeout: int = Field(default=5, description="连接超时(秒)")
    retry_on_timeout: bool = Field(default=True, description="超时重试")


class RedisConfig(ConfigSection):
    """Redis配置"""

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")

    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=6379, ge=1, le=65535, description="端口号")
    db: int = Field(default=0, ge=0, description="数据库编号")
    password: (str) | None = Field(default=None, alias="REDIS_PASSWORD", description="密码")
    pool: RedisPoolConfig = Field(default_factory=RedisPoolConfig, description="连接池配置")


class MemoryConfig(ConfigSection):
    """内存缓存配置"""

    max_size: int = Field(default=1000, description="最大缓存项数")
    ttl: int = Field(default=3600, description="默认过期时间(秒)")


class MemcachedConfig(ConfigSection):
    """Memcached配置"""

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")

    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=11211, ge=1, le=65535, description="端口号")
    connect_timeout: int = Field(default=5, description="连接超时(秒)")
    timeout: int = Field(default=5, description="操作超时(秒)")


@Component
@Singleton
class CacheConfig(ConfigSection):
    """
    缓存配置（由 IOC 容器管理单例）

    支持从 YAML 自动加载配置
    配置优先级：环境变量 > YAML 文件 > Field 默认值
    """

    yaml_config_file: ClassVar[str] = "config/repositories.yaml"
    yaml_config_key: ClassVar[str] = "cache"

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")

    type: str = Field(default="memory", description="缓存类型：redis、memory、memcached")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis配置")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="内存缓存配置")
    memcached: MemcachedConfig = Field(default_factory=MemcachedConfig, description="Memcached配置")


__all__ = [
    "RedisPoolConfig",
    "RedisConfig",
    "MemoryConfig",
    "MemcachedConfig",
    "CacheConfig",
]
