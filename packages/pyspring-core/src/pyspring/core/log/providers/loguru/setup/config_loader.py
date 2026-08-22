"""
配置加载器 - 从YAML加载日志配置

职责：仅负责加载和提取配置，不涉及handler设置
"""

from typing import Any

from ..config.manager import LoggingConfigManager


class ConfigLoader:
    """
    配置加载器

    负责从YAML文件加载日志配置并提取各部分配置。
    职责单一：只读取配置，不设置handler。
    """

    @classmethod
    def load_logging_config(cls) -> dict[str, Any]:
        """
        从YAML配置文件加载日志配置

        Returns:
            dict[str, Any]: 日志配置字典
        """
        config_manager = LoggingConfigManager()
        return config_manager.get("logging", {})

    @classmethod
    def get_console_config(cls, config: (dict[str, Any]) | None = None) -> dict[str, Any]:
        """
        获取控制台配置

        Args:
            config: 日志配置字典，如果为None则重新加载

        Returns:
            dict[str, Any]: 控制台配置
        """
        if config is None:
            config = cls.load_logging_config()

        return config.get("console", {})

    @classmethod
    def get_file_config(cls, config: (dict[str, Any]) | None = None) -> dict[str, Any]:
        """
        获取文件配置

        Args:
            config: 日志配置字典，如果为None则重新加载

        Returns:
            dict[str, Any]: 文件配置
        """
        if config is None:
            config = cls.load_logging_config()

        return config.get("file", {})

    @classmethod
    def get_context_config(cls, config: (dict[str, Any]) | None = None) -> dict[str, Any]:
        """
        获取上下文配置

        Args:
            config: 日志配置字典，如果为None则重新加载

        Returns:
            dict[str, Any]: 上下文配置
        """
        if config is None:
            config = cls.load_logging_config()

        return config.get("context", {})

    @classmethod
    def get_intercept_config(cls, config: (dict[str, Any]) | None = None) -> dict[str, Any]:
        """
        获取拦截配置

        Args:
            config: 日志配置字典，如果为None则重新加载

        Returns:
            dict[str, Any]: 拦截配置
        """
        if config is None:
            config = cls.load_logging_config()

        return config.get("intercept", {})

    @classmethod
    def get_level(cls, config: (dict[str, Any]) | None = None) -> str:
        """
        获取日志级别

        Args:
            config: 日志配置字典，如果为None则重新加载

        Returns:
            str: 日志级别
        """
        if config is None:
            config = cls.load_logging_config()

        return config.get("level", "INFO")

    @classmethod
    def get_advanced_config(cls, config: (dict[str, Any]) | None = None) -> dict[str, Any]:
        """
        获取高级配置（backtrace, diagnose等）

        Args:
            config: 日志配置字典，如果为None则重新加载

        Returns:
            dict[str, Any]: 高级配置
        """
        if config is None:
            config = cls.load_logging_config()

        return config.get("advanced", {})
