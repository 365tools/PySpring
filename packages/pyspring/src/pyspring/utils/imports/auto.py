"""
Auto Import Tool

Provides functionality to automatically import all modules under a package
"""
import importlib
import pkgutil
from typing import Dict, Any


def import_package(package_name: str, globals_dict: Dict[str, Any] = None, exclude: list = None) -> list:
    """
    Automatically import all modules under a package
    
    Args:
        package_name: Name of the package
        globals_dict: Global namespace (optional), if provided will be automatically updated
        exclude: List of module names to exclude (optional)
        
    Returns:
        list: 导出的符号列表
    """
    exported = {}
    exclude = exclude or []

    try:
        # 导入包
        package = importlib.import_module(package_name)

        # 获取包路径
        if hasattr(package, '__path__'):
            # 遍历包下的所有模块
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                if modname in exclude:
                    continue
                    
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
                except Exception as e:
                    # 忽略无法导入的模块（包括 SyntaxError, ImportError 等），保证 CLI 等工具能正常启动
                    # 在开发环境下，IDE 会提示具体的错误，或者通过单独运行模块/测试来发现
                    pass
    except Exception:
        # 忽略无法导入的包
        pass

    if globals_dict is not None:
        globals_dict.update(exported)

    return sorted(list(exported.keys()))
