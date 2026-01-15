"""
Check for unresolved references and optionally fix them.
"""
import ast
import builtins
import os
from collections import defaultdict
from typing import Optional, List, Set, Tuple

from pyspring.cli.component.files.ignore import get_ignore_list
from pyspring.cli.core.ui import (
    print_title, print_file_header, print_issue, print_summary,
    print_success, print_warning
)

# --- Knowledge Base for Auto-Fix ---
# Map symbol_name -> import_line
KNOWN_IMPORTS = {
    # Standard Library Common Modules
    "os": "import os",
    "sys": "import sys",
    "re": "import re",
    "json": "import json",
    "time": "import time",
    "math": "import math",
    "random": "import random",
    "datetime": "import datetime",
    "logging": "import logging",
    "argparse": "import argparse",
    "ast": "import ast",
    "inspect": "import inspect",
    "pathlib": "import pathlib",
    "shutil": "import shutil",
    "subprocess": "import subprocess",
    "threading": "import threading",
    "asyncio": "import asyncio",
    "functools": "import functools",
    "itertools": "import itertools",
    "collections": "import collections",
    "abc": "import abc",
    "types": "import types",
    "typing": "import typing",
    "traceback": "import traceback",
    "importlib": "import importlib",
    "uuid": "import uuid",
    "hashlib": "import hashlib",
    "base64": "import base64",
    "io": "import io",
    "csv": "import csv",
    "contextlib": "import contextlib",

    # 3rd Party
    "text": "from sqlalchemy import text",
    "create_engine": "from sqlalchemy import create_engine",
    "exclude": "from sqlalchemy.sql.expression import exclude",

    # Typing Types (Common)
    "List": "from typing import List",
    "Dict": "from typing import Dict",
    "Set": "from typing import Set",
    "Tuple": "from typing import Tuple",
    "Optional": "from typing import Optional",
    "Union": "from typing import Union",
    "Any": "from typing import Any",
    "Callable": "from typing import Callable",
    "Iterable": "from typing import Iterable",
    "Sequence": "from typing import Sequence",
    "Mapping": "from typing import Mapping",
    "Type": "from typing import Type",
    "ClassVar": "from typing import ClassVar",
    "Generator": "from typing import Generator",
    "TypeVar": "from typing import TypeVar",
    "Generic": "from typing import Generic",
    "cast": "from typing import cast",
    "overload": "from typing import overload",
    "NoReturn": "from typing import NoReturn",

    # Pathlib
    "Path": "from pathlib import Path",
}

BUILTINS = set(dir(builtins))


class Scope:
    """作用域管理"""

    def __init__(self, parent: Optional['Scope'] = None, is_class_scope: bool = False):
        self.parent = parent
        self.defined: Set[str] = set()
        self.is_class_scope = is_class_scope
        self.star_imported = False

    def define(self, name: str):
        self.defined.add(name)

    def is_defined(self, name: str) -> bool:
        if name in self.defined:
            return True
        if self.parent:
            # For simplicity, we allow looking up in parent scope even for classes
            return self.parent.is_defined(name)
        return False

    def has_star_import(self) -> bool:
        if self.star_imported:
            return True
        if self.parent:
            return self.parent.has_star_import()
        return False


class UnresolvedVisitor(ast.NodeVisitor):
    def __init__(self):
        self.current_scope = Scope()
        # Add builtins to global scope
        for b in BUILTINS:
            self.current_scope.define(b)

        # Add special module variables
        for special in ['__file__', '__path__', '__name__', '__doc__', '__package__']:
            self.current_scope.define(special)

        self.unresolved: List[Tuple[str, int, int]] = []  # (name, lineno, col_offset)

    def visit_FunctionDef(self, node):
        self.current_scope.define(node.name)

        # 1. Visit Decorators (Outer Scope)
        for decorator in node.decorator_list:
            self.visit(decorator)

        # 2. Visit Defaults (Outer Scope)
        for default in node.args.defaults:
            self.visit(default)
        for default in node.args.kw_defaults:
            if default: self.visit(default)

        # 3. Visit Annotations (Outer Scope)
        if node.returns:
            self.visit(node.returns)
        for arg in node.args.args + getattr(node.args, 'posonlyargs', []) + getattr(node.args, 'kwonlyargs', []):
            if arg.annotation: self.visit(arg.annotation)
        if node.args.vararg and node.args.vararg.annotation: self.visit(node.args.vararg.annotation)
        if node.args.kwarg and node.args.kwarg.annotation: self.visit(node.args.kwarg.annotation)

        # Enter New Scope
        prev_scope = self.current_scope
        self.current_scope = Scope(parent=prev_scope)

        # Define Arguments (Inner Scope)
        all_args = []
        all_args.extend(node.args.args)
        if hasattr(node.args, 'posonlyargs'):
            all_args.extend(node.args.posonlyargs)
        if hasattr(node.args, 'kwonlyargs'):
            all_args.extend(node.args.kwonlyargs)

        for arg in all_args:
            self.current_scope.define(arg.arg)

        if node.args.vararg: self.current_scope.define(node.args.vararg.arg)
        if node.args.kwarg: self.current_scope.define(node.args.kwarg.arg)

        # Visit Body (Inner Scope)
        for stmt in node.body:
            self.visit(stmt)

        self.current_scope = prev_scope

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self.current_scope.define(node.name)

        # Visit Bases and Keywords (Outer Scope)
        for base in node.bases:
            self.visit(base)
        for kw in node.keywords:
            self.visit(kw)

        # Visit Decorators (Outer Scope)
        for decorator in node.decorator_list:
            self.visit(decorator)

        # Enter Class Body Scope
        prev_scope = self.current_scope
        self.current_scope = Scope(parent=prev_scope, is_class_scope=True)

        # Visit Body
        for stmt in node.body:
            self.visit(stmt)

        self.current_scope = prev_scope

    def visit_Lambda(self, node):
        # Lambda defaults are Outer Scope
        for default in node.args.defaults:
            self.visit(default)
        for default in node.args.kw_defaults:
            if default: self.visit(default)

        prev_scope = self.current_scope
        self.current_scope = Scope(parent=prev_scope)

        for arg in node.args.args:
            self.current_scope.define(arg.arg)
        # add other args types if Lambda supports them (it does)
        if hasattr(node.args, 'posonlyargs'):
            for arg in node.args.posonlyargs: self.current_scope.define(arg.arg)
        if hasattr(node.args, 'kwonlyargs'):
            for arg in node.args.kwonlyargs: self.current_scope.define(arg.arg)
        if node.args.vararg: self.current_scope.define(node.args.vararg.arg)
        if node.args.kwarg: self.current_scope.define(node.args.kwarg.arg)

        self.visit(node.body)
        self.current_scope = prev_scope

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            self.current_scope.define(name)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name == '*':
                self.current_scope.star_imported = True
            else:
                name = alias.asname if alias.asname else alias.name
                self.current_scope.define(name)

    def visit_Global(self, node):
        for name in node.names:
            self.current_scope.define(name)

    def visit_Nonlocal(self, node):
        for name in node.names:
            self.current_scope.define(name)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Param)):
            self.current_scope.define(node.id)
        elif isinstance(node.ctx, ast.Load):
            if not self.current_scope.is_defined(node.id) and not self.current_scope.has_star_import():
                self.unresolved.append((node.id, node.lineno, node.col_offset))

    def visit_Attribute(self, node):
        self.visit(node.value)  # Only check if the base object is defined

    def visit_ExceptHandler(self, node):
        if node.name:
            self.current_scope.define(node.name)
        self.generic_visit(node)

    # Comprehensions
    def visit_ListComp(self, node):
        self._visit_comprehension(node)

    def visit_SetComp(self, node):
        self._visit_comprehension(node)

    def visit_DictComp(self, node):
        self._visit_comprehension(node)

    def visit_GeneratorExp(self, node):
        self._visit_comprehension(node)

    def _visit_comprehension(self, node):
        prev_scope = self.current_scope
        self.current_scope = Scope(parent=prev_scope)
        for generator in node.generators:
            self.visit(generator)
        if hasattr(node, 'elt'): self.visit(node.elt)
        if hasattr(node, 'key'): self.visit(node.key)
        if hasattr(node, 'value'): self.visit(node.value)
        self.current_scope = prev_scope

    def visit_comprehension(self, node):
        self.visit(node.iter)  # Iter is Outer Scope (or previous generator scope)
        self.visit(node.target)  # Target is Inner Scope (store)
        for if_ in node.ifs:
            self.visit(if_)


def scan_file(file_path: str) -> List[Tuple[str, int, int]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    visitor = UnresolvedVisitor()
    visitor.visit(tree)
    # Deduplicate by line
    return list(set(visitor.unresolved))


def apply_fixes(file_path: str, unresolved: List[Tuple[str, int, int]]) -> int:
    """
    Attempts to fix unresolved references by adding imports.
    Returns number of fixes applied.
    """
    # Map import_string -> min_line_needed
    needed_imports = {}
    for name, line, _ in unresolved:
        if name in KNOWN_IMPORTS:
            imp_stmt = KNOWN_IMPORTS[name]
            if imp_stmt not in needed_imports or line < needed_imports[imp_stmt]:
                needed_imports[imp_stmt] = line

    if not needed_imports:
        return 0

    # Use AST to find existing imports and their locations
    existing_imports = {}  # Map import_string -> min_lineno
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imp_str = f"import {alias.name}"
                    if imp_str not in existing_imports or node.lineno < existing_imports[imp_str]:
                        existing_imports[imp_str] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    name = alias.name
                    if module:
                        imp_str = f"from {module} import {name}"
                    else:
                        imp_str = f"from {name} import ..."

                    if imp_str not in existing_imports or node.lineno < existing_imports[imp_str]:
                        existing_imports[imp_str] = node.lineno

    except SyntaxError:
        # Fallback to text scan if syntax error prevents parsing
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        existing_imports = {line.strip(): 1 for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')}

    imports_to_add = []
    lines_to_remove_candidates = []  # List of (lineno, import_string)

    for imp, need_line in needed_imports.items():
        imp_clean = imp.strip()

        # Determine if we should add it
        should_add = False

        if imp_clean not in existing_imports:
            should_add = True
        else:
            # It exists, but is it early enough?
            # If the existing import is AFTER the first usage, we need to add it (hoist it)
            existing_line = existing_imports[imp_clean]
            if existing_line > need_line:
                should_add = True
                # Mark for potential removal
                lines_to_remove_candidates.append((existing_line, imp_clean))

        if should_add:
            imports_to_add.append(imp + '\n')

    if not imports_to_add:
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Process removals first
    indices_to_drop = set()
    for lineno, imp_content in lines_to_remove_candidates:
        if lineno <= 0 or lineno > len(lines):
            continue

        line_content = lines[lineno - 1].strip()
        # Remove comments for comparison
        line_content_no_comment = line_content.split('#')[0].strip()

        if line_content_no_comment == imp_content:
            indices_to_drop.add(lineno - 1)

    if indices_to_drop:
        lines = [line for i, line in enumerate(lines) if i not in indices_to_drop]

    # logic to insert imports
    # 1. Find the docstring end
    insert_idx = 0
    if len(lines) > 0 and (lines[0].startswith('"""') or lines[0].startswith("'''")):
        # Simple heuristic to skip docstring
        in_docstring = True
        for i, line in enumerate(lines):
            if i == 0: continue
            if '"""' in line or "'''" in line:
                insert_idx = i + 1
                break

    # Sort imports to be nice
    imports_to_add.sort()

    new_lines = lines[:insert_idx] + imports_to_add + lines[insert_idx:]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return len(imports_to_add)


def run_check_references(args):
    print_title("Checking Unresolved References")

    cwd = os.getcwd()
    target_dir = getattr(args, 'path', '.')  # Default to current dir if not provided
    target_dir = os.path.abspath(target_dir)  # Ensure absolute path

    if not os.path.exists(target_dir):
        print_warning(f"目标目录不存在: {target_dir}")
        return

    issues_found = 0
    fixed_count = 0

    files_with_issues = defaultdict(list)

    if os.path.isfile(target_dir):
        # Single file check
        if target_dir.endswith('.py'):
            unresolved = scan_file(target_dir)
            if unresolved:
                unresolved.sort(key=lambda x: x[1])
                files_with_issues[target_dir] = unresolved
                issues_found += len(unresolved)
    else:
        # Determine strict ignore set from current dir .gitignore + defaults
        ignore_set = get_ignore_list(cwd)

        for root, dirs, files in os.walk(target_dir):
            # Exclude common noise
            dirs[:] = [d for d in dirs if d not in ignore_set]

            for file in files:
                if not file.endswith('.py'):
                    continue

                file_path = os.path.join(root, file)
                unresolved = scan_file(file_path)

                if unresolved:
                    # Sort by lineno
                    unresolved.sort(key=lambda x: x[1])
                    files_with_issues[file_path] = unresolved
                    issues_found += len(unresolved)

    if not files_with_issues:
        print_summary(0, 0, 0, fixable=False)
        return

    for file_path, errors in files_with_issues.items():
        print_file_header(file_path)
        
        for name, line, col in errors:
            msg = f"未解决的引用 '{name}' (col {col})"
            print_issue(str(line), msg, file_path, level='error')

            if args.fix and name in KNOWN_IMPORTS:
                # 显示提示 (可选)
                pass

        if args.fix:
            applied = apply_fixes(file_path, errors)
            if applied > 0:
                print_success(f"     ✨ Applied {applied} fixes.")
                fixed_count += applied

    print_summary(issues_found, len(files_with_issues), fixed_count, fixable=not args.fix)
