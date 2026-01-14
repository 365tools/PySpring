import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger as _loguru

from pyspring.core.interfaces.ISingleton import ISingletonService
from pyspring.log.core.interface import ILoggerService
from pyspring.log.providers.loguru.config.manager import LoggingConfigManager


class _BoundLogger(ILoggerService):
    """一个轻量代理：在调用时同时应用深度定位与绑定的 extra"""

    def __init__(self, base_service: "LoguruService", extra: Dict[str, Any]):
        # ...existing code...
        self._base = base_service
        self._extra = dict(extra or {})

    def _opt_bind(self):
        # 通过公共方法避免访问受保护成员
        return self._base.with_context(**self._extra)

    def info(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().info(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().debug(message, *args, **kwargs)

    def trace(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().trace(message, *args, **kwargs)

    def success(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().success(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().warning(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().exception(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().critical(message, *args, **kwargs)

    def log(self, level: int, message: str, *args, **kwargs) -> Any:
        return self._opt_bind().log(level, message, *args, **kwargs)

    def bind(self, *args, **kwargs) -> Any:
        # ...existing code...
        new_extra = dict(self._extra)
        new_extra.update(kwargs or {})
        return _BoundLogger(self._base, new_extra)


class LoguruService(ISingletonService, ILoggerService):
    """Loguru 日志服务（由 IoC 容器管理单例）"""
    _configured = False

    def __init__(self):
        """初始化日志服务并配置日志"""
        if not self._configured:
            self._setup_logging()
            self.__class__._configured = True

    @staticmethod
    def _detect_project_root() -> Path:
        """检测项目根目录"""
        current = Path(__file__).resolve()

        # 向上查找，找到包含 'src' 的路径
        if "src" in current.parts:
            return Path(*current.parts[:current.parts.index("src")])

        # 否则向上查找标志文件
        while current != current.parent:
            if (current / "pyproject.toml").exists() or \
                    (current / "setup.py").exists() or \
                    (current / ".git").exists():
                return current
            current = current.parent

        return Path.cwd()

    @staticmethod
    def _add_relative_path(record):
        """为日志记录添加相对路径字段"""
        if "file_relative" not in record["extra"]:
            try:
                project_root = LoguruService._detect_project_root()
                file_path = Path(record["file"].path)
                relative_path = file_path.relative_to(project_root)
                record["extra"]["file_relative"] = str(relative_path)
            except (ValueError, AttributeError):
                record["extra"]["file_relative"] = record["file"].name
        return record

    def _setup_logging(self):
        """从配置文件设置日志"""
        config_manager = LoggingConfigManager()
        logging_config = config_manager.get('logging', {})

        # 移除默认处理器
        _loguru.remove()

        # 控制台配置
        console_config = logging_config.get('console', {})
        if console_config.get('enabled', True):
            _loguru.add(
                sys.stdout,
                format=console_config.get('format', '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'),
                level=logging_config.get('level', 'INFO'),
                colorize=console_config.get('colorize', True),
                backtrace=logging_config.get('advanced', {}).get('backtrace', True),
                diagnose=logging_config.get('advanced', {}).get('diagnose', True),
                enqueue=logging_config.get('advanced', {}).get('enqueue', False),
                filter=self._add_relative_path
            )

        # 文件日志配置
        file_config = logging_config.get('file', {})
        if file_config.get('enabled', False):
            project_root = self._detect_project_root()
            log_path = project_root / file_config.get('path', 'logs/app.log')

            # 确保日志目录存在
            log_path.parent.mkdir(parents=True, exist_ok=True)

            _loguru.add(
                str(log_path),
                format=file_config.get('format', '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}'),
                level=logging_config.get('level', 'INFO'),
                rotation=file_config.get('rotation', '10 MB'),
                retention=file_config.get('retention', '7 days'),
                compression=file_config.get('compression', 'zip'),
                backtrace=logging_config.get('advanced', {}).get('backtrace', True),
                diagnose=logging_config.get('advanced', {}).get('diagnose', True),
                enqueue=logging_config.get('advanced', {}).get('enqueue', True),
                filter=self._add_relative_path
            )

    # 保留常量占位，若未来需要扩展可再启用动态跳过策。
    _SKIP_MODULE_PREFIXES = (
        __name__,
        "src.pyspring.log.core.interface",
        "src.pyspring.log.instance",
        "src.pyspring.log",
        "src.pyspring.log.providers.loguru.utils.context",
    )
    _MAX_DEPTH = 25

    def _opt(self):
        """固定 depth=1：精准定位到调用 LoguruService/BoundLogger 的直接业务调用点。
        动态扫描在复杂调用链下易越级，导致文件/行号跳转不一致，故改为稳定策略。
        """
        return _loguru.opt(depth=1)

    def with_context(self, **extra) -> Any:
        return self._opt().bind(**(extra or {}))

    def info(self, message: str, *args, **kwargs) -> Any:
        return self._opt().info(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> Any:
        return self._opt().error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> Any:
        return self._opt().debug(message, *args, **kwargs)

    def trace(self, message: str, *args, **kwargs) -> Any:
        return self._opt().trace(message, *args, **kwargs)

    def success(self, message: str, *args, **kwargs) -> Any:
        return self._opt().success(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> Any:
        return self._opt().warning(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> Any:
        return self._opt().exception(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> Any:
        return self._opt().critical(message, *args, **kwargs)

    def log(self, level: int, message: str, *args, **kwargs) -> Any:
        return self._opt().log(level, message, *args, **kwargs)

    def bind(self, *args, **kwargs) -> Any:
        return _BoundLogger(self, kwargs or {})
