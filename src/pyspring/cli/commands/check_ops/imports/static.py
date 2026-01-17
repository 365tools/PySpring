"""
Static AST-based Import Checker Utilities
"""
import ast
import importlib.machinery
import importlib.util
import os
import sys
from typing import List


def is_module_available(module_name: str, sys_path: list) -> bool:
    """Check if module is available without importing it"""
    # 1. Check sys.modules cache
    if module_name in sys.modules:
        return True

    # 2. Check built-ins
    if module_name in sys.builtin_module_names:
        return True

    # 3. Use importlib machinery to search in specific path
    try:
        top_level = module_name.split('.')[0]
        # Use PathFinder explicitly to respect the provided sys_path
        spec = importlib.machinery.PathFinder.find_spec(top_level, path=sys_path)
        return spec is not None
    except (ValueError, ImportError, AttributeError):
        return False


def check_relative_import_exists(file_path: str, module_name: str, level: int) -> bool:
    """
    Check if a relative import target exists on the file system.
    level=1: same dir (.)
    level=2: parent dir (..)
    """
    current_dir = os.path.dirname(file_path)

    # Go up (level - 1) times
    # level=1 => 0 times (stay in current dir)
    target_dir = current_dir
    for _ in range(level - 1):
        target_dir = os.path.dirname(target_dir)

    # Convert dot-notation module name to path components
    # e.g. "sub.mod" -> "sub/mod"
    rel_path_components = module_name.split('.')
    path_without_ext = os.path.join(target_dir, *rel_path_components)

    # Check 1: path/to/module.py
    if os.path.exists(path_without_ext + '.py'):
        return True

    # Check 2: path/to/module/__init__.py
    if os.path.exists(os.path.join(path_without_ext, '__init__.py')):
        return True

    return False


class SymbolDefinitionVisitor(ast.NodeVisitor):
    def __init__(self, target_symbol: str):
        self.target_symbol = target_symbol
        self.found = False

    def visit_ClassDef(self, node: ast.ClassDef):
        if node.name == self.target_symbol:
            self.found = True

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name == self.target_symbol:
            self.found = True

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if node.name == self.target_symbol:
            self.found = True


def find_symbol_in_package(package_dir: str, symbol: str) -> List[str]:
    """
    Search for a symbol in .py files within the package (excluding __init__.py).
    If found, returns a list of all sub-module names where the symbol is found.
    """
    found_modules = []
    if not os.path.exists(package_dir):
        return []

    for root, _, files in os.walk(package_dir):
        # Currently only scans top-level child files of the package dir
        if root != package_dir:
            continue

        for file in files:
            if file == '__init__.py' or not file.endswith('.py'):
                continue

            file_path = str(os.path.join(root, file))
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Perform quick string check first
                if symbol not in content:
                    continue

                tree = ast.parse(content)
                visitor = SymbolDefinitionVisitor(symbol)
                visitor.visit(tree)

                if visitor.found:
                    found_modules.append(file[:-3])
            except Exception:
                continue

    return found_modules
