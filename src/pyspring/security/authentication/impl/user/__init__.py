"""
自动导入模块
"""
from utils.auto_import import auto_import_package

# 执行自动导入
_exported_items = auto_import_package(__name__)

# 更新全局命名空间
globals().update(_exported_items)
