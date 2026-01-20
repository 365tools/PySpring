"""
基于loguru的现代化日志系统
采用主流的loguru解决方案，支持YAML配置
"""
import importlib
import logging
import os
import re
import sys
import time
from pathlib import Path

from loguru import logger

from pyspring.core.context.registry import ContextRegistry
from .manager import LoggingConfigManager

# 全局存储为了兼容性自动注入的默认值 (key: default_value)
# 使用模块级变量以确保在多进程(Spawn)重建模块时，只要运行了setup就能访问
_AUTO_INJECTED_DEFAULTS = {}

# 全局存储上下文变量定义 (key, var_path, default_val)
_CONTEXT_VARS_DEFINITIONS = []

# 全局缓存已解析的 ContextVar 对象
_CTX_VARS_CACHE = {}

# 全局项目根目录缓存 (解决 LoguruConfig circular reference 问题)
_PROJECT_ROOT = None


def global_record_patcher(record):
    """
    全局 Loguru Patcher
    用于在日志记录产生时，动态注入上下文变量和缺失字段的默认值。
    替代之前的 filter 副作用方案，更稳健且支持多进程。
    """
    # 1. 注入 file_relative
    if "file_relative" not in record["extra"]:
        try:
            # 尝试从 record['file'].path 计算
            path_obj = Path(record["file"].path)
            # 优先使用全局缓存的 root
            root = _PROJECT_ROOT
            if root:
                record["extra"]["file_relative"] = str(path_obj.relative_to(root))
            else:
                record["extra"]["file_relative"] = record["file"].name
        except (ValueError, AttributeError):
            record["extra"]["file_relative"] = record["file"].name

    # 2. 注入自动补全的默认值 (修复 Legacy Config KeyError)
    for k, v in _AUTO_INJECTED_DEFAULTS.items():
        if k not in record["extra"]:
            record["extra"][k] = v

    # 3. 注入动态上下文变量
    # 优先使用缓存
    active_vars = []
    defs_key = tuple(tuple(x) for x in _CONTEXT_VARS_DEFINITIONS)

    if defs_key in _CTX_VARS_CACHE:
        active_vars = _CTX_VARS_CACHE[defs_key]
    else:
        # 首次解析
        temp = []
        for key, var_path, default_val in _CONTEXT_VARS_DEFINITIONS:
            try:
                if var_path:
                    module_name, var_name = var_path.rsplit('.', 1)
                    module = importlib.import_module(module_name)
                    ctx_var = getattr(module, var_name)
                    temp.append((key, ctx_var, default_val))
            except Exception:
                pass
        _CTX_VARS_CACHE[defs_key] = temp
        active_vars = temp

    # 执行注入
    for key, ctx_var, default_val in active_vars:
        if key not in record["extra"]:
            try:
                val = ctx_var.get()
            except (LookupError, AttributeError):
                val = None
            record["extra"][key] = val if val is not None else default_val


class LoguruConfig:
    """loguru日志系统配置管理类"""

    configured = False
    project_root = None

    # _yaml_context_vars 已废弃，使用 _CONTEXT_VARS_DEFINITIONS

    @classmethod
    def _get_active_context_vars(cls):
        """合并 YAML 配置和核心注册表的变量"""
        # 从核心获取所有代码注册的变量
        registry_vars = ContextRegistry.get_all()

        # 使用字典去重
        merged = {}

        # 1. 先放 Global Definitions (YAML 加载的)
        global _CONTEXT_VARS_DEFINITIONS
        for key, var_path, default_val in _CONTEXT_VARS_DEFINITIONS:
            # 这里我们无法直接获取 ContextVar 对象，除非重新 import
            # 但既然是兼容性方法，且主要用于调试或 introspection，我们可以尝试重建
            try:
                if var_path:
                    module_name, var_name = var_path.rsplit('.', 1)
                    module = importlib.import_module(module_name)
                    ctx_var = getattr(module, var_name)
                    merged[key] = (key, ctx_var, default_val)
            except Exception:
                pass

        # 2. 再放 Core Registry 的 (覆盖前者)
        for item in registry_vars:
            merged[item[0]] = item

        return list(merged.values())

    @classmethod
    def _resolve_context_vars(cls, logging_config: dict):
        """解析上下文变量配置"""
        global _CONTEXT_VARS_DEFINITIONS
        _CONTEXT_VARS_DEFINITIONS.clear()

        context_config = logging_config.get('context', {})
        fields = context_config.get('fields', [])

        # 默认回退：始终确保 trace_id 存在 (除非 YAML 已显式定义)
        # 这样用户无需在 logging.yaml 中配置基础 trace_id
        has_trace_id = any(f.get('key') == 'trace_id' for f in fields)
        if not has_trace_id:
            fields.append({
                "key": "trace_id",
                "var": "pyspring.log.providers.loguru.utils.trace_context._trace_id_ctx",
                "default": "sys"
            })

        for field in fields:
            key = field.get('key')
            var_path = field.get('var')
            default_val = field.get('default', "")

            if not key or not var_path:
                continue

            # 更新全局定义
            _CONTEXT_VARS_DEFINITIONS.append((key, var_path, default_val))

        # 旧的 _yaml_context_vars 和 logging_config 注入已不再需要

    @classmethod
    def _detect_project_root(cls) -> Path:
        """检测项目根目录"""
        global _PROJECT_ROOT
        
        if cls.project_root is not None:
            _PROJECT_ROOT = cls.project_root
            return cls.project_root

        try:
            p = Path(__file__).resolve()
        except NameError:
            p = Path.cwd()

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

        _PROJECT_ROOT = cls.project_root
        return cls.project_root

    @classmethod
    def _auto_register_missing_extra_fields(cls, logging_config: dict):
        """
        解析配置中的 format 字符串，自动发现未注册的 extra 字段并注册默认值为 N/A
        防止因配置引用了不存在的 extra 字段导致 Crash
        """

        # 1. 收集所有配置中使用的 format 字符串
        formats = []
        console_fmt = logging_config.get('console', {}).get('format')
        if console_fmt:
            formats.append(console_fmt)

        file_fmt = logging_config.get('file', {}).get('format')
        if file_fmt:
            formats.append(file_fmt)

        # 2. 正则提取 {extra[xxx]} 和 {xxx}
        # 匹配模式： {extra[key]} 或 {extra[key]:fmt}
        pattern_extra = re.compile(r'\{extra\[([a-zA-Z0-9_]+)\](?:[^}]*)?\}')
        # 匹配模式： {key} 或 {key:fmt} 或 {key!r}
        pattern_generic = re.compile(r'\{([a-zA-Z0-9_]+)(?:[:!][^}]*)?\}')

        needed_keys = set()
        for fmt in formats:
            # 提取 {extra[key]} 形式
            needed_keys.update(pattern_extra.findall(fmt))
            # 提取 {key} 形式
            needed_keys.update(pattern_generic.findall(fmt))

        # 3. 检查当前已激活的变量
        # 也不再依赖 cls._get_active_context_vars，而是看全局定义
        active_keys = {item[0] for item in _CONTEXT_VARS_DEFINITIONS}

        # 内置特殊字段不需要注册 (Loguru 保留关键字 + 自定义扩展字段)
        reserved_keys = {
            'time', 'level', 'message', 'module', 'file', 'line', 'function',
            'name', 'process', 'thread', 'elapsed', 'exception', 'extra',
            'file_relative'
        }
        active_keys.update(reserved_keys)

        # 4. 为缺失的字段注册占位符
        missing_keys = needed_keys - active_keys

        global _AUTO_INJECTED_DEFAULTS
        if missing_keys:
            for key in missing_keys:
                _AUTO_INJECTED_DEFAULTS[key] = "N/A"

    @classmethod
    def setup_from_yaml(cls, force: bool = False) -> None:
        """
        从YAML配置文件配置loguru日志系统

        Args:
            force: 是否强制重新配置
        """
        # ... (此处省略重复检查代码，保持原样逻辑但我们需要确保每次都更新 patcher 数据) ...
        # 但如果是 process spawn，类属性会被重置，configured 为 False，所以肯定会执行。

        # 更精确的重复配置检查
        if cls.configured and not force:
            return

        current_time = time.time()
        if hasattr(cls, '_last_config_time'):
            if current_time - cls._last_config_time < 1.0:
                # 即使跳过，也要确保 project_root 被初始化，否则 patcher 可能拿不到
                cls._detect_project_root()
                logger.debug(f"⏱️ 跳过1秒内的重复日志系统配置")
                return

        cls._last_config_time = current_time

        # 必须先初始化 project_root，供 patcher 使用
        cls._detect_project_root()

        # 加载配置
        config_manager = LoggingConfigManager()
        logging_config = config_manager.get('logging', {})

        # 解析上下文变量配置 -> 更新全局 _CONTEXT_VARS_DEFINITIONS
        cls._resolve_context_vars(logging_config)

        # 自动提取配置中 format 字符串里引用的 extra 字段 -> 更新全局 _AUTO_INJECTED_DEFAULTS
        cls._auto_register_missing_extra_fields(logging_config)

        # 移除所有现有的日志系统处理器
        logger.remove()

        # 核心修改：使用 configure(patcher=...) 替代 filter
        # 这会应用于所有后续添加的 handler
        logger.configure(patcher=global_record_patcher)

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
                filter=lambda record: cls._filter_logs(record, logging_config)
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
                filter=lambda record: cls._filter_logs(record, logging_config)
            )

        # 配置标准库logging的拦截
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

                # Use optional frame handling
                frame = sys._getframe(6)
                depth = 6
                while frame and frame.f_code.co_filename == logging.__file__:
                    if frame.f_back:
                        frame = frame.f_back
                        depth += 1
                    else:
                        break

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

        # 如果是绝对路径，直接返回
        file_path_obj = Path(file_path)
        if file_path_obj.is_absolute():
            return file_path

        # Ensure project root is detected
        root = cls._detect_project_root()
        
        # 对于相对路径，直接基于项目根目录拼接，避免重复'logs/logs'
        # 示例：file_path='logs/dev.log' => '<project_root>/logs/dev.log'
        resolved = root / file_path
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
        logger.configure(patcher=global_record_patcher)
        logger.add(
            sys.stdout,
            format=fmt,
            level=level,
            colorize=colorize,
            backtrace=backtrace,
            diagnose=diagnose,
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
