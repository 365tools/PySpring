"""
数据库配置 - Infrastructure层

通用的数据库配置类，支持多种数据库类型。
可在不同项目中复用。
"""
from typing import Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from pyspring.core.config.base import ConfigSection


class DatabasePoolConfig(ConfigSection):
    """数据库连接池配置"""
    model_config = SettingsConfigDict(extra='ignore')

    size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")
    recycle: int = Field(default=3600, description="连接回收时间(秒)")
    timeout: int = Field(default=30, description="连接超时时间(秒)")
    pre_ping: bool = Field(default=True, description="连接前ping检查")


class PostgreSQLConfig(ConfigSection):
    """PostgreSQL配置"""
    model_config = SettingsConfigDict(populate_by_name=True)

    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=5432, ge=1, le=65535, description="端口号")
    database: str = Field(default="app_db", description="数据库名")
    user: Optional[str] = Field(default=None, alias="POSTGRES_USER", description="用户名")
    password: Optional[str] = Field(default=None, alias="POSTGRES_PASSWORD", description="密码")
    pool: DatabasePoolConfig = Field(default_factory=DatabasePoolConfig, description="连接池配置")


class MySQLConfig(ConfigSection):
    """MySQL配置"""
    model_config = SettingsConfigDict(populate_by_name=True)

    host: str = Field(default="localhost", description="主机地址")
    port: int = Field(default=3306, ge=1, le=65535, description="端口号")
    database: str = Field(default="app_db", description="数据库名")
    user: Optional[str] = Field(default=None, alias="MYSQL_USER", description="用户名")
    password: Optional[str] = Field(default=None, alias="MYSQL_PASSWORD", description="密码")
    charset: str = Field(default="utf8mb4", description="字符集")
    pool: DatabasePoolConfig = Field(default_factory=DatabasePoolConfig, description="连接池配置")


class SQLiteConfig(ConfigSection):
    """SQLite配置"""
    model_config = SettingsConfigDict(extra='ignore')

    database: str = Field(default="data/app.db", description="数据库文件路径")
    pool: DatabasePoolConfig = Field(default_factory=DatabasePoolConfig, description="连接池配置")


class DatabaseConfig(ConfigSection):
    """通用数据库配置"""
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
