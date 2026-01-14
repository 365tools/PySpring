"""
系统配置模型 - 统一配置入口

聚合所有配置类，提供统一的配置访问接口。
所有具体配置类从各模块引用，避免重复定义。
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from pyspring.core.config.base import ConfigSection
# 从各子系统导入配置类
from pyspring.log.core.config import LoggingConfig
from pyspring.repositories.cache.config import RedisConfig, CacheConfig
from pyspring.repositories.db.config import DatabaseConfig
from pyspring.security.authorization.rabc.schema.config import JWTConfig, AuthenticationConfig


# ==================== 应用基础配置（仅定义顶层应用相关配置）====================

class ServerConfig(ConfigSection):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", description="服务器地址")
    port: int = Field(default=8000, ge=1, le=65535, description="服务器端口")
    debug: bool = Field(default=False, description="调试模式")
    reload: bool = Field(default=False, description="自动重载")
    workers: int = Field(default=1, ge=1, description="工作进程数")
    log_level: str = Field(default="INFO", description="Uvicorn服务器日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL")


class AppConfig(ConfigSection):
    """应用配置"""
    name: str = Field(default="PySpring Application", description="应用名称")
    version: str = Field(default="1.0.0", description="应用版本")
    description: str = Field(default="", description="应用描述")
    environment: str = Field(default="development", description="运行环境：development, production, test")
    server: ServerConfig = Field(default_factory=ServerConfig, description="服务器配置")


# ==================== 主配置类 ====================

class AppSettings(BaseSettings):
    """
    应用配置主类
    
    聚合所有配置，自动从以下来源加载（优先级从高到低）：
    1. 环境变量
    2. .env 文件
    3. config/*.yaml 文件
    4. 默认值
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )

    # 应用配置
    app: AppConfig = Field(default_factory=AppConfig, description="应用配置")

    # 数据库配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")

    # Redis配置
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis配置")

    # 日志配置
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置")

    # 认证配置
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig, description="认证配置")


# ==================== 单例配置实例 ====================

# 全局配置实例（单例）
settings = AppSettings()

__all__ = [
    "AppSettings",
    "AppConfig",
    "ServerConfig",
    # 从其他模块引用的配置类
    "JWTConfig",
    "AuthenticationConfig",
    "DatabaseConfig",
    "RedisConfig",
    "CacheConfig",
    "LoggingConfig",
    # 单例实例
    "settings",
]
