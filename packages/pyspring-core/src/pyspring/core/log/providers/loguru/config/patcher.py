"""
日志记录 Patcher - 动态注入上下文变量和默认值

在日志记录产生时，动态注入上下文变量和缺失字段的默认值。
支持多进程环境，替代之前的 filter 副作用方案。
"""
import importlib
from contextvars import ContextVar
from pathlib import Path
from typing import Any, cast

# 全局存储自动注入的默认值
_AUTO_INJECTED_DEFAULTS: dict[str, Any] = {}

# 全局存储上下文变量定义 (key, var_path, default_val)
_CONTEXT_VARS_DEFINITIONS: list[tuple[str, str, Any]] = []

# 全局缓存已解析的 ContextVar 对象
_CTX_VARS_CACHE: dict[tuple[tuple[str, str, Any], ...], list[tuple[str, ContextVar[object], Any]]] = {}

# 全局项目根目录缓存
_PROJECT_ROOT: (Path) | None = None


def set_project_root(root: Path):
    """设置项目根目录（供 patcher 使用）"""
    global _PROJECT_ROOT
    _PROJECT_ROOT = root


def set_auto_injected_defaults(defaults: dict[str, Any]):
    """设置自动注入的默认值"""
    global _AUTO_INJECTED_DEFAULTS
    _AUTO_INJECTED_DEFAULTS.clear()
    _AUTO_INJECTED_DEFAULTS.update(defaults)


def set_context_vars_definitions(definitions: list[tuple[str, str, Any]]):
    """设置上下文变量定义"""
    global _CONTEXT_VARS_DEFINITIONS
    _CONTEXT_VARS_DEFINITIONS.clear()
    _CONTEXT_VARS_DEFINITIONS.extend(definitions)
    # 清空缓存，强制重新解析
    _CTX_VARS_CACHE.clear()


def global_record_patcher(record):
    """
    全局 Loguru Patcher
    
    用于在日志记录产生时，动态注入上下文变量和缺失字段的默认值。
    替代之前的 filter 副作用方案，更稳健且支持多进程。
    
    Args:
        record: Loguru 日志记录对象
    """
    # 1. 注入 file_relative
    if "file_relative" not in record["extra"]:
        try:
            path_obj = Path(record["file"].path)
            # 优先使用全局缓存的 root
            root = _PROJECT_ROOT
            if root:
                relative_path = str(path_obj.relative_to(root)).replace("\\", "/")
                record["extra"]["file_relative"] = relative_path
            else:
                # 回退到完整文件名（包含扩展名）
                record["extra"]["file_relative"] = path_obj.name
        except (ValueError, AttributeError):
            # 最终回退到完整文件名
            record["extra"]["file_relative"] = Path(record["file"].path).name

    # 2. 注入自动补全的默认值
    for k, v in _AUTO_INJECTED_DEFAULTS.items():
        if k not in record["extra"]:
            record["extra"][k] = v

    # 3. 注入动态上下文变量
    # 优先使用缓存
    active_vars = []
    defs_key = cast(tuple[tuple[str, str, Any], ...], tuple(tuple(x) for x in _CONTEXT_VARS_DEFINITIONS))

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


__all__ = [
    "global_record_patcher",
    "set_project_root",
    "set_auto_injected_defaults",
    "set_context_vars_definitions",
]
