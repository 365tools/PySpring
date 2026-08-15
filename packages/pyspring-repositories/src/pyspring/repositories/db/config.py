"""
数据库配置 - Infrastructure层

通用的数据库配置类，支持多种数据库类型。
可在不同项目中复用。
"""
from typing import ClassVar

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from pyspring.core.abstracts.config import ConfigSection
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton


class DatabasePoolConfig(ConfigSection):
    """数据库连接池配置"""
    yaml_config_file: ClassVar[str] = "config/repositories.yaml"
    yaml_config_key: ClassVar[str] = "database.pool"
    
    model_config = SettingsConfigDict(extra='ignore')

    size: int = Field(default=5, ge=1, le=100, description="连接池大小")
    max_overflow: int = Field(default=10, ge=0, le=50, description="最大溢出连接数")
    recycle: int = Field(default=3600, ge=0, le=86400, description="连接回收时间(秒)")
    timeout: int = Field(default=30, ge=1, le=300, description="连接超时时间(秒)")
    pre_ping: bool = Field(default=True, description="连接前ping检查")
    pool_pre_ping: bool = Field(default=True, description="连接池预检查")
    pool_recycle: int = Field(default=3600, ge=0, le=86400, description="连接池回收时间(秒)")
    pool_timeout: int = Field(default=30, ge=1, le=300, description="连接池获取连接超时时间(秒)")
    echo: bool = Field(default=False, description="SQL日志输出")
    pool_reset_on_return: str = Field(default="commit", description="返回连接时的重置行为")


class PostgreSQLConfig(ConfigSection):
    """PostgreSQL配置"""
    yaml_config_file: ClassVar[str] = "config/repositories.yaml"
    yaml_config_key: ClassVar[str] = "database.postgresql"

    model_config = SettingsConfigDict(populate_by_name=True, extra='ignore')

    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=5432, ge=1, le=65535, description="端口号")
    database: str = Field(default="app_db", description="数据库名")
    user: (str) | None = Field(default=None, alias="POSTGRES_USER", description="用户名")
    password: (str) | None = Field(default=None, alias="POSTGRES_PASSWORD", description="密码")
    pool: DatabasePoolConfig = Field(default_factory=DatabasePoolConfig, description="连接池配置")


class MySQLConfig(ConfigSection):
    """MySQL配置"""
    yaml_config_file: ClassVar[str] = "config/repositories.yaml"
    yaml_config_key: ClassVar[str] = "database.mysql"

    model_config = SettingsConfigDict(populate_by_name=True, extra='ignore')

    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=3306, ge=1, le=65535, description="端口号")
    database: str = Field(default="app_db", description="数据库名")
    user: (str) | None = Field(default=None, alias="MYSQL_USER", description="用户名")
    password: (str) | None = Field(default=None, alias="MYSQL_PASSWORD", description="密码")
    charset: str = Field(default="utf8mb4", description="字符集")
    pool: DatabasePoolConfig = Field(default_factory=DatabasePoolConfig, description="连接池配置")


class SQLiteConfig(ConfigSection):
    """SQLite配置"""
    yaml_config_file: ClassVar[str] = "config/repositories.yaml"
    yaml_config_key: ClassVar[str] = "database.sqlite"
    
    model_config = SettingsConfigDict(extra='ignore')

    database: str = Field(default="data/app.db", description="数据库文件路径")
    pool: DatabasePoolConfig = Field(default_factory=DatabasePoolConfig, description="连接池配置")


@Component
@Singleton
class DatabaseConfig(ConfigSection):
    """通用数据库配置"""
    yaml_config_file: ClassVar[str] = "config/repositories.yaml"
    yaml_config_key: ClassVar[str] = "database"

    model_config = SettingsConfigDict(extra='ignore')

    type: str = Field(default="sqlite", description="数据库类型：postgresql、mysql、sqlite")
    postgresql: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig, description="PostgreSQL配置")
    mysql: MySQLConfig = Field(default_factory=MySQLConfig, description="MySQL配置")
    sqlite: SQLiteConfig = Field(default_factory=SQLiteConfig, description="SQLite配置")


__all__ = [
    "DatabasePoolConfig",
    "PostgreSQLConfig",
    "MySQLConfig",
    "SQLiteConfig",
    "DatabaseConfig",
]
