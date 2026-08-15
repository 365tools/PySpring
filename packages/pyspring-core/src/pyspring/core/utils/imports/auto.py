"""
Auto Import Tool

Provides functionality to automatically import all modules under a package

注意：
- 本模块是基础设施层，被 pyspring/__init__.py 及各子包 __init__.py 调用。
- 使用 Python 标准库 logging（而非 pyspring.log），避免形成循环导入。
- 默认启用严格模式：模块导入失败立即抛出，避免静默掩盖循环依赖。
"""
import importlib
import logging
import pkgutil
from typing import Any

logger = logging.getLogger(__name__)


def import_package(
    package_name: str,
    globals_dict: dict[str, Any] | None = None,
    exclude: list[str] | None = None,
    strict: bool = True,
) -> list[str]:
    """
    Automatically import all modules under a package.

    Args:
        package_name: Name of the package
        globals_dict: Global namespace (optional), if provided will be automatically updated
        exclude: List of module names to exclude (optional)
        strict: If True, a module import failure raises immediately; if False,
                the failure is logged (warning) and skipped. Default True.

    Returns:
        list: 导出的符号列表
    """
    exported: dict[str, Any] = {}
    exclude_set = set(exclude or [])

    try:
        # 导入包
        package = importlib.import_module(package_name)
    except Exception:
        if strict:
            raise
        logger.warning("无法导入包: %s", package_name, exc_info=True)
        return []

    # 获取包路径
    if not hasattr(package, "__path__"):
        return []

    # 遍历包下的所有模块
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        if modname in exclude_set:
            continue

        try:
            # 导入模块
            module = importlib.import_module(f"{package_name}.{modname}")

            # 导出模块中的公共符号
            if hasattr(module, "__all__"):
                for name in module.__all__:
                    exported[name] = getattr(module, name)
            else:
                # 如果没有 __all__，导出所有不以下划线开头的符号
                for name in dir(module):
                    if not name.startswith("_"):
                        exported[name] = getattr(module, name)
        except Exception as e:
            if strict:
                raise
            # 非严格模式下：记录失败（含 traceback），便于定位而非静默掩盖
            logger.warning(
                "导入模块失败: %s.%s - %s: %s",
                package_name, modname, type(e).__name__, e,
            )

    if globals_dict is not None:
        globals_dict.update(exported)

    return sorted(list(exported.keys()))
