"""
Static AST-based Import Checker
"""
import ast
import importlib.util
import os
import sys
from typing import List

from pyspring.cli.component.files.ignore import get_ignore_list
from pyspring.cli.core.ui import print_error


class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        # List of dict: {'module': str, 'lineno': int, 'level': int}
        self.imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({'module': alias.name, 'lineno': node.lineno, 'level': 0})
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        level = node.level if node.level is not None else 0
        if node.module:
            self.imports.append({'module': node.module, 'lineno': node.lineno, 'level': level})
        else:
            # Relative import without module, eg 'from . import x'
            # Here 'x' is in node.names
            for alias in node.names:
                self.imports.append({'module': alias.name, 'lineno': node.lineno, 'level': level})
        self.generic_visit(node)


def find_python_files(root_dir: str) -> List[str]:
    py_files = []
    ignored = get_ignore_list(os.getcwd())

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored]
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files


def is_module_available(module_name: str, sys_path: list) -> bool:
    """Check if module is available without importing it"""
    # 1. Check sys.modules cache
    if module_name in sys.modules:
        return True

    # 2. Check built-ins
    if module_name in sys.builtin_module_names:
        return True

    # 3. Use find_spec (requires the module path to be in sys.path)
    try:
        top_level = module_name.split('.')[0]
        spec = importlib.util.find_spec(top_level)
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


def run_ast_check(target_path: str):
    print(f"Running Static Analysis (AST) on: {target_path}...\n")

    files = find_python_files(target_path)
    if not files:
        print("No Python files found.")
        return

    sys_path = sys.path
    # Ensure current dir and src are in path for lookup
    cwd = os.getcwd()
    if cwd not in sys_path:
        sys_path.insert(0, cwd)
    src_path = os.path.join(cwd, 'src')
    if os.path.exists(src_path) and src_path not in sys_path:
        sys_path.insert(0, src_path)

    total_files = 0
    issues_found = 0

    for file_path in files:
        total_files += 1
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=file_path)
            visitor = ImportVisitor()
            visitor.visit(tree)

            # Check collected imports
            file_issues = []

            for imp in visitor.imports:
                mod_name = imp['module']
                lineno = imp['lineno']
                level = imp['level']

                is_valid = True
                if level > 0:
                    # Relative Import
                    if not check_relative_import_exists(file_path, mod_name, level):
                        is_valid = False
                else:
                    # Absolute Import
                    if not is_module_available(mod_name, sys_path):
                        is_valid = False

                if not is_valid:
                    file_issues.append((mod_name, lineno))

            if file_issues:
                issues_found += 1
                rel_path = os.path.relpath(file_path, cwd)
                print(f"❌ {rel_path}")
                for mod, line in file_issues:
                    print(f"   Line {line}: Module '{mod}' not found")
                    print(f"   Path: {file_path}:{line}")

        except SyntaxError as e:
            issues_found += 1
            print(f"❌ Syntax Error in {os.path.relpath(file_path, cwd)}: {e}")
        except Exception as e:
            print(f"warning: could not parse {file_path}: {e}")

    print("\n" + "-" * 50)
    if issues_found:
        print_error(f"Static check finished. Issues found in {issues_found}/{total_files} files.")
        print("Note: Static analysis checks top-level packages. Dynamic imports might still fail at runtime.")
        sys.exit(1)
    else:
        print(f"✅ Static check passed! Scanned {total_files} files.")
        print("(Verifies that top-level packages of all imports exist in environment)")
