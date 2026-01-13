"""
自动导入模块
"""
from utils.auto_import import auto_import_package

__all__ = auto_import_package(__name__, globals(), exclude=['main'])
