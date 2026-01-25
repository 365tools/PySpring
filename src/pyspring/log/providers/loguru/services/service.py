import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger as _loguru
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.interfaces.core import IManaged
from pyspring.log.core.interface import ILoggerService

from ..config.manager import LoggingConfigManager


class _SafeExtraDict(dict):
    """安全的 extra 字典，访问不存在的键时返回空字符串而不是抛出 KeyError"""

    def __missing__(self, key):
        """当访问不存在的键时返回空字符串"""
        return ""

    def __getitem__(self, key):
        """重写 __getitem__ 以支持 __missing__"""
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)


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


@Component()
@Singleton
class LoguruService(IManaged, ILoggerService):
    """Loguru 日志服务（由IOC容器管理单例）"""
    _configured = False

    def __init__(self):
        """初始化日志服务"""
        self._setup_logging()

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
        """
        为日志记录添加相对路径字段，并将 extra 包装为 SafeDict
        
        智能路径处理：
        - 框架代码：显示简化路径，如 [fw] db.factory:123
        - 用户代码：显示完整相对路径，如 app.services.auth_service:45
        
        使用 _SafeExtraDict 包装 extra 字典，这样在日志格式中使用任何
        不存在的字段时都不会抛出 KeyError，而是返回空字符串。
        
        这使得日志配置更加灵活和健壮：
        - 用户可以在格式中使用任何字段（如 session_id, request_id 等）
        - 如果字段不存在，显示为空而不是报错
        - 可以通过 logger.bind() 随时添加字段值
        """
        # 确保 extra 字典存在
        if "extra" not in record:
            record["extra"] = _SafeExtraDict()
        elif not isinstance(record["extra"], _SafeExtraDict):
            # 将现有的 extra 字典包装为 SafeDict
            record["extra"] = _SafeExtraDict(record["extra"])

        # 只在字段不存在时添加 file_relative
        if "file_relative" not in record["extra"]:
            try:
                file_path = Path(record["file"].path)
                path_parts = file_path.parts

                # 检测是否是 PySpring 框架代码
                is_framework = "pyspring" in path_parts

                if is_framework:
                    # 框架代码：简化显示
                    # 找到 pyspring 之后的路径部分
                    pyspring_idx = path_parts.index("pyspring")
                    relevant_parts = path_parts[pyspring_idx + 1:]  # pyspring 之后的部分

                    # 转换为模块路径格式：repositories/db/factory.py → db.factory
                    if len(relevant_parts) > 0:
                        # 移除文件扩展名
                        module_parts = list(relevant_parts[:-1]) + [relevant_parts[-1].replace('.py', '')]
                        # 只保留最后2-3级，使其简洁
                        if len(module_parts) > 3:
                            module_parts = module_parts[-3:]
                        module_path = ".".join(module_parts)
                        record["extra"]["file_relative"] = f"[fw] {module_path}"
                    else:
                        record["extra"]["file_relative"] = "[fw] pyspring"
                else:
                    # 用户代码：显示详细路径
                    project_root = LoguruService._detect_project_root()
                    try:
                        relative_path = file_path.relative_to(project_root)
                        # 转换为模块路径格式：app/services/auth.py → app.services.auth
                        path_str = str(relative_path).replace('\\', '/')
                        module_path = path_str.replace('.py', '').replace('/', '.')
                        record["extra"]["file_relative"] = module_path
                    except ValueError:
                        # 如果无法计算相对路径，使用文件名
                        module_name = file_path.stem
                        record["extra"]["file_relative"] = f"app.{module_name}"
                        
            except (ValueError, AttributeError, KeyError):
                # 安全回退：使用文件名
                try:
                    record["extra"]["file_relative"] = record["file"].name
                except (AttributeError, KeyError):
                    record["extra"]["file_relative"] = "unknown"
        
        return record

    def _setup_logging(self):
        """从配置文件设置日志"""
        # 先移除默认处理器并应用临时配置（带 filter），避免配置加载期间的日志使用默认格式
        _loguru.remove()
        _loguru.add(
            sys.stdout,
            format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[file_relative]}</cyan>:<cyan>{line}</cyan> | {message}',
            level='DEBUG',
            colorize=True,
            filter=self._add_relative_path
        )

        # 现在可以安全地加载配置（日志已应用 filter）
        config_manager = LoggingConfigManager()
        logging_config = config_manager.get('logging', {})

        # 移除临时处理器，应用最终配置
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

        # 如果从文件加载了配置，记录一条调试日志
        if hasattr(config_manager, '_loaded_config_path') and config_manager._loaded_config_path:
            # 使用 debug 级别，这样在 info 级别下默认不显示，实现了“静默”
            _loguru.debug(f"✅ 已加载日志配置: {config_manager._loaded_config_path}")

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