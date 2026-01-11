"""
日志配置 - Infrastructure层

通用的日志配置类，可在不同项目中复用。
"""
from pydantic import Field

from pyspring.core.config.base import ConfigSection


class ConsoleLoggingConfig(ConfigSection):
    """控制台日志配置"""
    enabled: bool = Field(default=True, description="是否启用")
    colorize: bool = Field(default=True, description="彩色输出")
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}",
        description="日志格式"
    )


class FileLoggingConfig(ConfigSection):
    """文件日志配置"""
    enabled: bool = Field(default=False, description="是否启用")
    path: str = Field(default="logs/app.log", description="日志文件路径")
    rotation: str = Field(default="10 MB", description="日志轮转大小")
    retention: str = Field(default="7 days", description="日志保留时间")
    compression: str = Field(default="zip", description="压缩格式")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        description="日志格式"
    )


class AdvancedLoggingConfig(ConfigSection):
    """高级日志配置"""
    backtrace: bool = Field(default=True, description="显示回溯信息")
    diagnose: bool = Field(default=True, description="诊断模式")
    enqueue: bool = Field(default=True, description="异步队列")


class LoggingFiltersConfig(ConfigSection):
    """日志过滤配置"""
    health_check: bool = Field(default=True, description="过滤健康检查")
    metrics: bool = Field(default=True, description="过滤指标")
    favicon: bool = Field(default=True, description="过滤favicon请求")


class LoggingInterceptConfig(ConfigSection):
    """日志拦截配置"""
    stdlib: bool = Field(default=True, description="拦截标准库日志")
    uvicorn: bool = Field(default=True, description="拦截uvicorn日志")
    fastapi: bool = Field(default=True, description="拦截fastapi日志")
    watchfiles: bool = Field(default=True, description="拦截watchfiles日志")


class LoggingConfig(ConfigSection):
    """通用日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    console: ConsoleLoggingConfig = Field(default_factory=ConsoleLoggingConfig, description="控制台配置")
    file: FileLoggingConfig = Field(default_factory=FileLoggingConfig, description="文件配置")
    advanced: AdvancedLoggingConfig = Field(default_factory=AdvancedLoggingConfig, description="高级配置")
    filters: LoggingFiltersConfig = Field(default_factory=LoggingFiltersConfig, description="过滤配置")
    intercept: LoggingInterceptConfig = Field(default_factory=LoggingInterceptConfig, description="拦截配置")


__all__ = [
    "ConsoleLoggingConfig",
    "FileLoggingConfig",
    "AdvancedLoggingConfig",
    "LoggingFiltersConfig",
    "LoggingInterceptConfig",
    "LoggingConfig",
]
