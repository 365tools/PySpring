"""
Handler构建器 - 构建和配置Loguru handlers

职责：负责根据配置构建控制台和文件handler
"""
import sys
from typing import Any

from loguru import logger
from pyspring.core.log.core.utils import detect_project_root

from ..config.filter import filter_logs
from ..config.patcher import global_record_patcher


class HandlerBuilder:
    """
    Handler构建器
    
    负责根据配置构建和添加各种handler到loguru。
    """

    @classmethod
    def build_console_handler(
            cls,
            config: dict[str, Any],
            level: str,
            advanced: dict[str, Any]
    ) -> None:
        """
        构建控制台handler
        
        Args:
            config: 控制台配置
            level: 日志级别
            advanced: 高级配置
        """
        if not config.get('enabled', True):
            return

        logger.add(
            sys.stdout,
            format=config.get(
                'format',
                '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
            ),
            level=level,
            colorize=config.get('colorize', True),
            backtrace=advanced.get('backtrace', True),
            diagnose=advanced.get('diagnose', True),
            filter=lambda record: filter_logs(record, {'console': config, 'level': level})
        )

    @classmethod
    def build_file_handler(
            cls,
            config: dict[str, Any],
            level: str,
            advanced: dict[str, Any]
    ) -> None:
        """
        构建文件handler
        
        Args:
            config: 文件配置
            level: 日志级别
            advanced: 高级配置
        """
        if not config.get('enabled', False):
            return

        # 解析文件路径
        project_root = detect_project_root()
        file_path = project_root / config.get('path', 'logs/app.log')

        # 确保日志目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(file_path),
            format=config.get(
                'format',
                '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}'
            ),
            level=level,
            rotation=config.get('rotation', '10 MB'),
            retention=config.get('retention', '7 days'),
            compression=config.get('compression', 'zip'),
            backtrace=advanced.get('backtrace', True),
            diagnose=advanced.get('diagnose', True),
            filter=lambda record: filter_logs(record, {'file': config, 'level': level})
        )

    @classmethod
    def setup_all_handlers(
            cls,
            console_config: dict[str, Any],
            file_config: dict[str, Any],
            level: str,
            advanced: dict[str, Any]
    ) -> None:
        """
        设置所有handlers
        
        Args:
            console_config: 控制台配置
            file_config: 文件配置
            level: 日志级别
            advanced: 高级配置
        """
        # 移除所有现有的日志处理器
        logger.remove()

        # 配置patcher（必须在add之前）
        logger.configure(patcher=global_record_patcher)

        # 添加控制台handler
        cls.build_console_handler(console_config, level, advanced)

        # 添加文件handler
        cls.build_file_handler(file_config, level, advanced)
