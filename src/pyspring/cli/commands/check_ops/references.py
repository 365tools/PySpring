"""
Check for unresolved references and optionally fix them.
"""
import ast
import builtins
import os
from collections import defaultdict
from typing import Optional, List, Set, Tuple

from pyspring.cli.core.ui import print_section, print_success, print_error, print_info

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

    # PySpring Common (Safe to add?)
    # Maybe logger? but user has custom logger.
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
    needed_imports = set()
    for name, _, _ in unresolved:
        if name in KNOWN_IMPORTS:
            needed_imports.add(KNOWN_IMPORTS[name])

    if not needed_imports:
        return 0

    # Use AST to find existing imports reliably, ignoring docstrings/comments
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            tree = ast.parse(code)

        existing_imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    existing_imports.add(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    name = alias.name
                    if module:
                        existing_imports.add(f"from {module} import {name}")
                    else:
                        existing_imports.add(f"from {name} import ...")  # approximation

        # Also simple text scan as fallback for lines that might look like imports but AST missed? 
        # No, AST is the authority. If AST checks valid code, it knows what is imported.

    except SyntaxError:
        # Fallback to text scan if syntax error prevents parsing
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        existing_imports = set(line.strip() for line in lines if line.strip().startswith('import ') or line.strip().startswith('from '))
        code = "".join(lines)  # needed later? No, we read it.

    imports_to_add = []
    for imp in needed_imports:
        # Check against existing to avoid duplication
        # Normalize imp string (strip newline)
        imp_clean = imp.strip()

        # Check if exactly this import statement exists
        if imp_clean in existing_imports:
            continue

        # Check if the module is already imported (e.g. 'import os' vs 'from os import path')
        # This is harder. simpler check:
        if imp_clean.startswith('import '):
            mod_name = imp_clean.split(' ')[1]
            # If "import os" is needed, and "import os" is in existing, we skip.
            # If "from os import path" is in existing, "os" is NOT defined as a name (unless "from os import path, os"? rare).
            pass

        imports_to_add.append(imp + '\n')

    if not imports_to_add:
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

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

    # If there are existing imports after docstring, try to merge with them?
    # For simplicity, we just insert at insert_idx

    # Sort imports to be nice
    imports_to_add.sort()

    new_lines = lines[:insert_idx] + imports_to_add + lines[insert_idx:]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return len(imports_to_add)


def run_check_references(args):
    print_section("Checking Unresolved References")

    cwd = os.getcwd()
    target_dir = getattr(args, 'path', '.')  # Default to current dir if not provided
    target_dir = os.path.abspath(target_dir)  # Ensure absolute path

    if not os.path.exists(target_dir):
        print_error(f"Target directory not found: {target_dir}")
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
        for root, dirs, files in os.walk(target_dir):
            # Exclude common noise
            dirs[:] = [d for d in dirs if d not in ('.venv', 'venv', '__pycache__', '.git', 'site-packages', 'node_modules')]

            for file in files:
                if not file.endswith('.py'):
                    continue

                file_path = os.path.join(root, file)
                unresolved = scan_file(file_path)

                if unresolved:
                    # Filter out likely false positives? 
                    # e.g. 'logger' if not imported but injected? (Though it should be imported)
                    # self, cls are handled by Visitor logic hopefully

                    # Sort by lineno
                    unresolved.sort(key=lambda x: x[1])
                    # Note: We used to rely on file_path relative to cwd, now absolute
                    files_with_issues[file_path] = unresolved
                    issues_found += len(unresolved)

    if not files_with_issues:
        print_success("No unresolved references found.")
        return

    for file_path, errors in files_with_issues.items():
        rel_path = os.path.relpath(file_path, cwd).replace('\\', '/')

        # Clickable link format: [path](path:line:col)
        # Note: Standard markdown link [text](url)
        # VS Code terminal link: outputting proper path allows clicking.

        print_info(f"File: {file_path}")
        for name, line, col in errors:
            # Output absolute path for clickable links in most IDE terminals
            # Format: absolute_path:line:col
            print(f"  ❌ Line {line}: Unresolved reference '{name}' -> {file_path}:{line}")

            if args.fix and name in KNOWN_IMPORTS:
                print(f"     💡 Auto-fix available: {KNOWN_IMPORTS[name]}")

        if args.fix:
            applied = apply_fixes(file_path, errors)
            if applied > 0:
                print_success(f"     ✨ Applied {applied} fixes.")
                fixed_count += applied

    print_section("Summary")
    print(f"Found {issues_found} unresolved references in {len(files_with_issues)} files.")
    if args.fix:
        print_success(f"Fixed {fixed_count} missing imports.")
    else:
        print_info("Tip: Run with --fix to automatically add missing standard library imports.")
