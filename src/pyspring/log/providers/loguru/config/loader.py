"""
Loguru 配置加载器 - 从 YAML 配置文件设置 Loguru

负责读取配置、解析上下文变量、配置 Loguru 处理器。
"""
import importlib
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from loguru import logger

from pyspring.core.context.registry import ContextRegistry
from .filter import filter_logs
from .interceptor import setup_stdlib_intercept
from .manager import LoggingConfigManager
from .patcher import (
    global_record_patcher,
    set_project_root,
    set_auto_injected_defaults,
    set_context_vars_definitions
)


class LoguruConfig:
    """
    Loguru 日志系统配置管理类
    
    负责从 YAML 配置文件加载配置并应用到 Loguru。
    """

    configured: bool = False
    project_root: Optional[Path] = None
    _last_config_time: float = 0

    @classmethod
    def _get_active_context_vars(cls) -> List[Tuple[str, Any, Any]]:
        """
        合并 YAML 配置和核心注册表的上下文变量
        
        Returns:
            List[Tuple[str, ContextVar, Any]]: (key, context_var, default) 列表
        """
        from .patcher import _CONTEXT_VARS_DEFINITIONS

        # 从核心获取所有代码注册的变量
        registry_vars = ContextRegistry.get_all()

        # 使用字典去重
        merged = {}

        # 1. 先放 Global Definitions (YAML 加载的)
        for key, var_path, default_val in _CONTEXT_VARS_DEFINITIONS:
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
    def _resolve_context_vars(cls, logging_config: Dict[str, Any]):
        """
        解析上下文变量配置
        
        Args:
            logging_config: 日志配置字典
        """
        context_vars_definitions = []

        context_config = logging_config.get('context', {})
        fields = context_config.get('fields', [])

        # 默认回退：始终确保 trace_id 存在 (除非 YAML 已显式定义)
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

            context_vars_definitions.append((key, var_path, default_val))

        # 更新全局定义
        set_context_vars_definitions(context_vars_definitions)

    @classmethod
    def _detect_project_root(cls) -> Path:
        """
        检测项目根目录
        
        Returns:
            Path: 项目根目录路径
        """
        if cls.project_root is not None:
            set_project_root(cls.project_root)
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

        set_project_root(cls.project_root)
        return cls.project_root

    @classmethod
    def _auto_register_missing_extra_fields(cls, logging_config: Dict[str, Any]):
        """
        解析配置中的 format 字符串，自动发现未注册的 extra 字段并注册默认值
        
        防止因配置引用了不存在的 extra 字段导致 Crash。
        
        Args:
            logging_config: 日志配置字典
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
        pattern_extra = re.compile(r'\{extra\[([a-zA-Z0-9_]+)\](?:[^}]*)?\}')
        pattern_generic = re.compile(r'\{([a-zA-Z0-9_]+)(?:[:!][^}]*)?\}')

        needed_keys = set()
        for fmt in formats:
            needed_keys.update(pattern_extra.findall(fmt))
            needed_keys.update(pattern_generic.findall(fmt))

        # 3. 检查当前已激活的变量
        from .patcher import _CONTEXT_VARS_DEFINITIONS
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

        auto_injected_defaults = {}
        if missing_keys:
            for key in missing_keys:
                auto_injected_defaults[key] = "N/A"

        set_auto_injected_defaults(auto_injected_defaults)

    @classmethod
    def setup_from_yaml(cls, force: bool = False) -> None:
        """
        从 YAML 配置文件配置 Loguru 日志系统
        
        Args:
            force: 是否强制重新配置
        """
        # 更精确的重复配置检查
        if cls.configured and not force:
            return

        current_time = time.time()
        if hasattr(cls, '_last_config_time'):
            if current_time - cls._last_config_time < 1.0:
                # 即使跳过，也要确保 project_root 被初始化
                cls._detect_project_root()
                logger.debug(f"⏱️ 跳过1秒内的重复日志系统配置")
                return

        cls._last_config_time = current_time

        # 必须先初始化 project_root，供 patcher 使用
        cls._detect_project_root()

        # 加载配置
        config_manager = LoggingConfigManager()
        logging_config = config_manager.get('logging', {})

        # 解析上下文变量配置
        cls._resolve_context_vars(logging_config)

        # 自动提取配置中 format 字符串里引用的 extra 字段
        cls._auto_register_missing_extra_fields(logging_config)

        # 移除所有现有的日志处理器
        logger.remove()

        # 核心修改：使用 configure(patcher=...) 替代 filter
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
                encoding='utf-8',  # 使用UTF-8编码输出，解决Windows下中文乱码
                filter=lambda record: filter_logs(record, logging_config)
            )

        # 文件日志配置
        file_config = logging_config.get('file', {})
        if file_config.get('enabled', False):
            project_root = cls._detect_project_root()
            file_path = project_root / file_config.get('path', 'logs/app.log')

            # 确保日志目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                str(file_path),
                format=file_config.get('format', '{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}'),
                level=logging_config.get('level', 'INFO'),
                rotation=file_config.get('rotation', '10 MB'),
                retention=file_config.get('retention', '7 days'),
                compression=file_config.get('compression', 'zip'),
                encoding='utf-8',  # 使用UTF-8编码写入文件，解决中文乱码
                backtrace=logging_config.get('advanced', {}).get('backtrace', True),
                diagnose=logging_config.get('advanced', {}).get('diagnose', True),
                filter=lambda record: filter_logs(record, logging_config)
            )

        # 配置标准库 logging 的拦截
        intercept_config = logging_config.get('intercept', {})
        if intercept_config.get('stdlib', True):
            setup_stdlib_intercept(intercept_config)

        cls.configured = True
        logger.debug(f"⚙️ Loguru 日志系统配置完成 - 级别: {logging_config.get('level', 'INFO')}")

    @classmethod
    def resolve_file_path(cls, file_path: str) -> str:
        """
        解析日志文件路径
        
        Args:
            file_path: 日志文件路径（可以是相对路径或绝对路径）
            
        Returns:
            str: 解析后的绝对路径
        """
        file_path_obj = Path(file_path)
        if file_path_obj.is_absolute():
            return file_path

        # 对于相对路径，基于项目根目录拼接
        root = cls._detect_project_root()
        resolved = root / file_path
        resolved.parent.mkdir(exist_ok=True, parents=True)
        return str(resolved)


__all__ = ["LoguruConfig"]
