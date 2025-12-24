"""
自动导入工具

提供自动导入包下所有模块的功能
"""
import importlib
import pkgutil
from typing import Dict, Any


def auto_import_package(package_name: str) -> Dict[str, Any]:
    """
    自动导入包下的所有模块
    
    Args:
        package_name: 包名
        
    Returns:
        dict: 导出的符号字典
    """
    exported = {}

    try:
        # 导入包
        package = importlib.import_module(package_name)

        # 获取包路径
        if hasattr(package, '__path__'):
            # 遍历包下的所有模块
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                try:
                    # 导入模块
                    module = importlib.import_module(f'{package_name}.{modname}')

                    # 导出模块中的公共符号
                    if hasattr(module, '__all__'):
                        for name in module.__all__:
                            exported[name] = getattr(module, name)
                    else:
                        # 如果没有 __all__，导出所有不以下划线开头的符号
                        for name in dir(module):
                            if not name.startswith('_'):
                                exported[name] = getattr(module, name)
                except ImportError:
                    # 忽略无法导入的模块
                    pass
    except ImportError:
        # 忽略无法导入的包
        pass

    return exported
