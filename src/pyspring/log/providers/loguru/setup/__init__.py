"""
Loguru配置设置模块

提供统一的配置入口，协调各个子模块完成日志系统配置。
"""
import time

from loguru import logger

from .config_loader import ConfigLoader
from .context_resolver import ContextResolver
from .field_scanner import FieldScanner
from .handler_builder import HandlerBuilder


class ConfiguratorFacade:
    """
    配置器门面 - 统一入口
    
    协调各个配置模块，提供单一的配置接口。
    采用门面模式简化复杂的配置流程。
    """

    _configured: bool = False
    _is_setting_up: bool = False  # 重入保护
    _last_config_time: float = 0

    @classmethod
    def setup(cls, force: bool = False) -> None:
        """
        设置日志系统
        
        完整的配置流程：
        1. 加载YAML配置
        2. 解析上下文变量
        3. 扫描并注册字段
        4. 配置patcher
        5. 设置handlers
        6. 配置stdlib拦截
        
        Args:
            force: 是否强制重新配置
        """
        # 重入保护
        if cls._is_setting_up:
            return

        # 避免重复配置
        if cls._configured and not force:
            return

        # 时间检查（1秒内不重复配置）
        current_time = time.time()
        if hasattr(cls, '_last_config_time'):
            time_diff = current_time - cls._last_config_time
            if time_diff < 1.0:
                # 即使跳过，也要确保project_root被初始化
                from pyspring.log.core.utils import detect_project_root
                from ..config.patcher import set_project_root
                project_root = detect_project_root()
                set_project_root(project_root)
                return

        # 设置重入保护标志
        cls._is_setting_up = True

        try:
            cls._last_config_time = current_time

            # 1. 初始化项目根目录（必须最先执行，供patcher使用）
            from pyspring.log.core.utils import detect_project_root
            from ..config.patcher import set_project_root
            project_root = detect_project_root()
            set_project_root(project_root)

            # 2. 加载配置
            logging_config = ConfigLoader.load_logging_config()

            # 3. 解析上下文变量
            context_vars_definitions = ContextResolver.resolve_context_vars(logging_config)
            ContextResolver.apply_context_config(context_vars_definitions)

            # 4. 自动扫描并注册字段
            FieldScanner.auto_register_from_config(logging_config)

            # 5. 设置所有handlers
            console_config = ConfigLoader.get_console_config(logging_config)
            file_config = ConfigLoader.get_file_config(logging_config)
            level = ConfigLoader.get_level(logging_config)
            advanced = ConfigLoader.get_advanced_config(logging_config)

            HandlerBuilder.setup_all_handlers(
                console_config=console_config,
                file_config=file_config,
                level=level,
                advanced=advanced
            )

            # 6. 配置标准库logging的拦截
            from ..config.interceptor import setup_stdlib_intercept
            intercept_config = ConfigLoader.get_intercept_config(logging_config)
            if intercept_config.get('stdlib', True):
                setup_stdlib_intercept(intercept_config)

            cls._configured = True
            logger.debug(f"⚙️ Loguru 日志系统配置完成 - 级别: {level}")

        finally:
            # 释放重入保护标志
            cls._is_setting_up = False

    @classmethod
    def is_configured(cls) -> bool:
        """
        检查是否已配置
        
        Returns:
            bool: 是否已配置
        """
        return cls._configured

    @classmethod
    def reset(cls) -> None:
        """
        重置配置状态
        
        主要用于测试场景。
        """
        cls._configured = False
        cls._is_setting_up = False
        cls._last_config_time = 0


__all__ = [
    'ConfiguratorFacade',
    'ConfigLoader',
    'HandlerBuilder',
    'ContextResolver',
    'FieldScanner'
]
