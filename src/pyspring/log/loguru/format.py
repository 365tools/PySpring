"""
基于loguru的现代化日志系统
采用主流的loguru解决方案，支持YAML配置
"""
import logging
import os
import sys
from pathlib import Path

from loguru import logger

from pyspring.log.loguru.config_manager import LoggingConfigManager


class LoguruConfig:
    """loguru日志系统配置管理类"""

    configured = False
    project_root = None

    @classmethod
    def _detect_project_root(cls) -> Path:
        """检测项目根目录"""
        if cls.project_root is not None:
            return cls.project_root

        p = Path(__file__).resolve()
        if "src" in p.parts:
            cls.project_root = Path(*p.parts[:p.parts.index("src")])
        else:
            # 向上查找标志文件
            current = p
            while current != current.parent:
                if (current / "pyproject.toml").exists() or \
                        (current / "setup.py").exists() or \
                        (current / ".git").exists():
                    cls.project_root = current
                    break
                current = current.parent
            else:
                cls.project_root = p.parents[5] if len(p.parents) >= 6 else p.parent.parent.parent

        return cls.project_root

    @classmethod
    def _add_relative_path_to_record(cls, record):
        """为记录添加相对路径字段和 session_id 默认值（不覆盖已有绑定）"""
        # file_relative：若已有，不覆盖；无则尝试计算
        if "file_relative" not in record["extra"]:
            try:
                file_path = Path(record["file"].path)
                # 计算相对于项目根目录的路径
                project_root = cls._detect_project_root()
                relative_path = file_path.relative_to(project_root)
                record["extra"]["file_relative"] = str(relative_path)
            except (ValueError, AttributeError):
                # 如果无法计算相对路径，使用文件名
                record["extra"]["file_relative"] = record["file"].name

        # session_id：若已通过 logger.bind(session_id=...) 绑定，不覆盖；否则从上下文读取
        sid_bound = record["extra"].get("session_id")
        if not sid_bound:
            try:
                from pyspring.log.loguru.context import _session_id_ctx
                sid_ctx = _session_id_ctx.get()
            except Exception as e:
                # 避免循环依赖，直接打印到stderr
                print(f"🚨 Error getting session_id: {e}", file=sys.stderr)
                sid_ctx = None
            record["extra"]["session_id"] = sid_ctx or "sys"
        return record

    @classmethod
    def setup_from_yaml(cls, force: bool = False) -> None:
        """
        从YAML配置文件配置loguru日志系统

        Args:
            force: 是否强制重新配置
        """
        # 更精确的重复配置检查
        if cls.configured and not force:
            return

        # 即使是force=True，也添加短时间内的重复调用检查
        import time
        current_time = time.time()
        if hasattr(cls, '_last_config_time'):
            if current_time - cls._last_config_time < 1.0:  # 1秒内的重复调用
                logger.debug(f"⏱️ 跳过1秒内的重复日志系统配置（距离上次: {current_time - cls._last_config_time:.3f}s)")
                return

        cls._last_config_time = current_time

        # 加载配置
        config_manager = LoggingConfigManager()
        logging_config = config_manager.get('logging', {})

        # 移除所有现有的日志系统处理器
        logger.remove()

        # 控制台配置
        console_config = logging_config.get('console', {})
        if console_config.get('enabled', True):
            logger.add(
                sys.stdout,
                format=console_config.get('format', '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'),
                level=logging_config.get('level', 'INFO'),
                colorize=console_config.get('colorize', True),
                backtrace=logging_config.get('advanced', {}).get('backtrace', True),
                diagnose=logging_config.get('advanced', {}).get('diagnose', True),
                filter=lambda record: cls._filter_logs(cls._add_relative_path_to_record(record), logging_config)
            )

        # 文件日志系统配置
        file_config = logging_config.get('file', {})
        if file_config.get('enabled', False):
            project_root = cls._detect_project_root()
            file_path = project_root / file_config.get('path', 'logs/app.log')

            # 确保日志系统目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                str(file_path),
                format=file_config.get('format', '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}'),
                level=logging_config.get('level', 'INFO'),
                rotation=file_config.get('rotation', '10 MB'),
                retention=file_config.get('retention', '7 days'),
                compression=file_config.get('compression', 'zip'),
                backtrace=logging_config.get('advanced', {}).get('backtrace', True),
                diagnose=logging_config.get('advanced', {}).get('diagnose', True),
                filter=lambda record: cls._filter_logs(cls._add_relative_path_to_record(record), logging_config)
            )

        # 配置标准库logging的拦)
        intercept_config = logging_config.get('intercept', {})
        if intercept_config.get('stdlib', True):
            cls._setup_stdlib_intercept(intercept_config)

        cls.configured = True
        logger.debug(f"⚙️ Loguru日志系统统配置完成 - 级别: {logging_config.get('level', 'INFO')}")

    @classmethod
    def _filter_logs(cls, record, logging_config) -> bool:
        """根据配置过滤日志系统记录"""
        message = record.get("message", "").lower()

        # 获取过滤器配置
        filters_config = logging_config.get('filters', {})
        
        # 根据配置进行过滤
        filter_rules = [
            (filters_config.get('health_check', True), "health"),
            (filters_config.get('metrics', True), "metrics"),
            (filters_config.get('favicon', True), "favicon.ico"),
        ]

        for filter_enabled, keyword in filter_rules:
            if filter_enabled and keyword in message:
                return False

        # 检查自定义过滤路径
        custom_paths = filters_config.get('custom_paths', [])
        for path in custom_paths:
            if path.lower() in message:
                return False

        return True

    @classmethod
    def _setup_stdlib_intercept(cls, intercept_config) -> None:
        """根据配置设置标准库logging的拦截器"""

        class InterceptHandler(logging.Handler):
            def emit(self, record):
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno

                frame, depth = sys._getframe(6), 6
                while frame and frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1

                logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )

        # 配置标准库logging
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

        # 获取根logger并强制使用我们的处理器
        root_logger = logging.getLogger()
        root_logger.handlers = [InterceptHandler()]
        root_logger.propagate = False
        root_logger.setLevel(0)

        # 根据配置决定要拦截的logger
        loggers_to_intercept = []

        if intercept_config.get('uvicorn', True):
            loggers_to_intercept.extend(["uvicorn", "uvicorn.error", "uvicorn.access"])

        if intercept_config.get('fastapi', True):
            loggers_to_intercept.append("fastapi")

        if intercept_config.get('watchfiles', True):
            # 除了拦截，还对watchfiles 的"changes detected"类消息做抑制
            # 默认启用抑制（新配置系统中暂无此配置项）
            suppress_changes = True

            class WatchfilesFilter(logging.Filter):
                def filter(self, record: logging.LogRecord) -> bool:
                    msg = str(record.getMessage()).lower()
                    if suppress_changes and "changes detected" in msg:
                        return False
                    return True

            loggers_to_intercept.extend(["watchfiles", "watchfiles.main"])
            for name in ["watchfiles", "watchfiles.main"]:
                lgr = logging.getLogger(name)
                lgr.addFilter(WatchfilesFilter())

        # 拦截自定义日志系统记录器
        custom_loggers = intercept_config.get('custom_loggers', [])
        loggers_to_intercept.extend(custom_loggers)

        for logger_name in loggers_to_intercept:
            stdlib_logger = logging.getLogger(logger_name)
            stdlib_logger.handlers = [InterceptHandler()]
            stdlib_logger.propagate = False
            stdlib_logger.setLevel(0)

    @classmethod
    def resolve_file_path(cls, file_path: str) -> str:
        """解析日志文件路径"""
        from pathlib import Path
        
        # 如果是绝对路径，直接返回
        file_path_obj = Path(file_path)
        if file_path_obj.is_absolute():
            return file_path
        # 对于相对路径，直接基于项目根目录拼接，避免重复'logs/logs'
        # 示例：file_path='logs/dev.log' => '<project_root>/logs/dev.log'
        resolved = cls.project_root / file_path
        resolved.parent.mkdir(exist_ok=True, parents=True)
        return str(resolved)

    @classmethod
    def setup(cls, level: str = "INFO", force: bool = False) -> None:
        """简化版设置接口，满足测试用例需求"""
        # 直接使用 setup_from_yaml
        cls.setup_from_yaml(force=force)

    @classmethod
    def add_file_handler(cls, file_path: str, level: str = "DEBUG", rotation: str = "1 MB", retention: str = "1 day") -> int:
        """添加文件日志处理器，返回handler id"""
        resolved = cls.resolve_file_path(file_path)
        handler_id = logger.add(
            resolved,
            level=level,
            rotation=rotation,
            retention=retention,
            enqueue=True,
        )
        return handler_id

    @classmethod
    def apply_simple_config(cls, *, level: str, fmt: str, colorize: bool, backtrace: bool, diagnose: bool, note: str) -> None:
        """应用简单配置（降级方案）"""
        logger.remove()
        logger.add(
            sys.stdout,
            format=fmt,
            level=level,
            colorize=colorize,
            backtrace=backtrace,
            diagnose=diagnose,
            filter=lambda record: cls._add_relative_path_to_record(record)
        )
        cls.configured = True
        logger.debug(note)


# 环境配置预设 - 旧版本已废弃，使用 YAML 配置替代
# 这些函数已被移除，因为 LoggerConfig 类不存在
# 请使用 LoguruConfig.setup_from_yaml() 进行配置

def configure_with_fallback(*, level: str, fmt: str, colorize: bool, backtrace: bool, diagnose: bool, note: str) -> None:
    """通用配置流程：优先从 YAML 配置；失败时降级为简单配置"""
    try:
        LoguruConfig.setup_from_yaml(force=True)
    except Exception as e:
        logger.error(f"🚨 配置日志系统失败: {e}")
        LoguruConfig.apply_simple_config(
            level=level,
            fmt=fmt,
            colorize=colorize,
            backtrace=backtrace,
            diagnose=diagnose,
            note=note,
        )


def configure_development():
    configure_with_fallback(
        level="DEBUG",
        fmt="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {file.name}:{line} in <cyan>{function}()</cyan> | <level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
        note="✅ 开发环境日志系统配置完成 - 级别: DEBUG",
    )


def configure_production():
    configure_with_fallback(
        level="INFO",
        fmt="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {file.name}:{line} in {function}() | {message}",
        colorize=False,
        backtrace=False,
        diagnose=False,
        note="✅ 生产环境日志系统配置完成 - 级别: INFO",
    )


def configure_testing():
    configure_with_fallback(
        level="WARNING",
        fmt="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {file.name}:{line} | <level>{message}</level>",
        colorize=True,
        backtrace=False,
        diagnose=False,
        note="✅ 测试环境日志系统配置完成 - 级别: WARNING",
    )


def auto_configure():
    """根据环境自动配置日志系统"""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        configure_production()
    elif env == "testing":
        configure_testing()
    else:
        configure_development()


# 新的配置驱动的初始化函数
def setup_logging_from_config(force: bool = False) -> None:
    """
    从全局配置初始化日志系统

    Args:
        force: 是否强制重新配置
    """
    try:
        LoguruConfig.setup_from_yaml(force=force)
    except Exception as e:
        logger.error(f"🚨 配置日志系统失败: {e}")
        # 降级到自动配置
        auto_configure()


# 模块导入时自动配置 - 使用新的配置系统
if not LoguruConfig.configured:
    setup_logging_from_config()


def add_file_handler(file_path: str, level: str = "DEBUG", rotation: str = "1 MB", retention: str = "1 day") -> int:
    """模块级文件日志添加函数，兼容测试用例"""
    return LoguruConfig.add_file_handler(file_path, level=level, rotation=rotation, retention=retention)

