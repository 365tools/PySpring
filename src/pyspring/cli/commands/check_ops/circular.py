"""
Circular Dependency Checker using AST
"""
import ast
import os
import sys
from collections import defaultdict
from typing import Dict, Set, Optional

from pyspring.cli.component.files.ignore import get_ignore_list
from pyspring.cli.core.ui import (
    print_title, print_summary,
    print_warning, print_info
)


class CircularDependencyChecker:
    def __init__(self, root_path: str, package_root: str = None):
        """
        :param root_path: The filesystem path to scan (e.g. ./src)
        :param package_root: The root package path (to resolve relative imports correctly)
                             If None, assumes root_path is the root.
        """
        self.root_path = os.path.abspath(root_path)
        self.package_root = os.path.abspath(package_root) if package_root else self.root_path
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.files: Dict[str, str] = {}  # module -> file_path
        self.modules: Dict[str, str] = {}  # file_path -> module

    def get_module_name(self, file_path: str) -> str:
        """Convert file path to dotted module name"""
        rel_path = os.path.relpath(file_path, self.package_root)
        if rel_path.startswith('..'):
            # fallback if file is outside package root
            rel_path = os.path.relpath(file_path, self.root_path)

        name = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
        if name.endswith('.__init__'):
            name = name[:-9]
        return name

    def scan(self):
        """Scan all python files and build dependency graph"""
        print_info(f"Scanning {self.root_path}...")

        ignore_list = get_ignore_list(os.getcwd())

        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ignore_list]

            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    module_name = self.get_module_name(full_path)
                    self.files[module_name] = full_path
                    self.modules[full_path] = module_name

                    try:
                        self._parse_file(full_path, module_name)
                    except Exception as e:
                        # Use file header for error context if needed
                        print_warning(f"Failed to parse {full_path}: {e}")

    def _parse_file(self, file_path: str, current_module: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read(), filename=file_path)
            except SyntaxError:
                return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.dependencies[current_module].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Absolute import or relative import with module base
                    if node.level == 0:
                        # Absolute: from pyspring.core import ...
                        target = node.module
                    else:
                        # Relative: from . import ... or from ..utils import ...
                        # Resolve relative import
                        target = self._resolve_relative_import(current_module, node.module, node.level)

                    if target:
                        self.dependencies[current_module].add(target)
                else:
                    # from . import module (node.module is None)
                    target = self._resolve_relative_import(current_module, None, node.level)
                    if target:
                        # This imports the __init__ of that package usually, 
                        # but often it is used to import submodules which are in 'names'
                        # e.g. from . import submodule
                        for alias in node.names:
                            self.dependencies[current_module].add(f"{target}.{alias.name}")

    def _resolve_relative_import(self, current_module: str, relative_name: Optional[str], level: int) -> Optional[str]:
        parts = current_module.split('.')
        # level=1 (from .), pop 0. level=2 (from ..), pop 1.
        if level > len(parts):
            # Import goes beyond top level
            return None

        base_parts = parts[:-level] if level > 0 else parts

        base = ".".join(base_parts)
        if relative_name:
            if base:
                return f"{base}.{relative_name}"
            else:
                return relative_name
        return base

    def _find_internal_module(self, import_name: str) -> Optional[str]:
        """
        Check if import_name maps to an internal module.
        """
        if import_name in self.files:
            return import_name

        # Check parent packages recursively? 
        # For circular dependency, strict match is safer to avoid false positives with libs
        return None

    def run_check(self) -> bool:
        """Returns True if no cycles found"""
        print_title("Circular Dependency Check")
        self.scan()

        print_info(f"Analyzed {len(self.files)} modules.")

        visited_global = set()
        path_stack = []
        path_set = set()

        found_cycles = []

        def dfs(node):
            if node in path_set:
                cycle = path_stack[path_stack.index(node):] + [node]
                found_cycles.append(cycle)
                return

            if node in visited_global:
                return

            visited_global.add(node)
            path_stack.append(node)
            path_set.add(node)

            for neighbor_raw in self.dependencies[node]:
                neighbor = self._find_internal_module(neighbor_raw)
                if neighbor:
                    dfs(neighbor)

            path_stack.pop()
            path_set.remove(node)

        # Sort for deterministic output
        for node in sorted(self.files.keys()):
            dfs(node)

        if not found_cycles:
            print_summary(0, 0, 0, fixable=False)
            return True

        # De-duplicate cycles (A->B->A is same as B->A->B)
        unique_cycles = set()
        count = 0

        # Print detailed cycles
        for cycle in found_cycles:
            # Normalize tuple
            # Rotate to start with smallest string
            min_node = min(cycle[:-1])
            start_idx = cycle.index(min_node)
            normalized = tuple(cycle[start_idx:-1] + cycle[:start_idx] + [min_node])

            if normalized in unique_cycles:
                continue
            unique_cycles.add(normalized)
            count += 1

            print(f"\nCycle {count}:")
            # Visual ASCII Arrow
            for i, mod in enumerate(cycle):
                prefix = "  "
                if i > 0: prefix = "  ↓ "
                print(f"{prefix}{mod}")

        # Summary
        print_summary(count, count, 0, fixable=False)  # Roughly file count is cycle count for this display
        return False


def run_check_circular(args):
    path = os.path.abspath(args.path)
    project_root = os.getcwd()

    # Smart detection for source root
    # If scanning project root and 'src' exists, treat 'src' as the package root
    # This ensures modules are named 'pyspring.xxx' instead of 'src.pyspring.xxx'
    package_root = None
    if path == project_root:
        src_path = os.path.join(project_root, 'src')
        if os.path.exists(src_path):
            package_root = src_path

    checker = CircularDependencyChecker(path, package_root=package_root)
    success = checker.run_check()
    if not success:
        print()
        print_title("Next Steps")
        print_info("To resolve circular dependencies:")
        print("  1. Refactor common logic into a separate module (common.py/utils.py)")
        print("  2. Move imports inside functions/methods (delayed import)")
        print("  3. Use 'pyspring check lift' to automatically move imports to top if safe")
        sys.exit(1)
