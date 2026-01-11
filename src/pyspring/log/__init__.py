"""
自动导入模块
"""
from utils.auto_import import auto_import_package

# 显式导出手动定义的工具
from pyspring.log.context_registry import register_context_var

# 执行自动导入
_exported_items = auto_import_package(__name__)

# 更新全局命名空间
globals().update(_exported_items)

# 生成 __all__
__all__ = sorted(list(_exported_items.keys()) + ["register_context_var"])
