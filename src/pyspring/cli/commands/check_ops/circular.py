"""
Circular Dependency Checker using AST
"""
import ast
import os
import sys
from collections import defaultdict
from typing import Dict, Set, List, Optional

from pyspring.cli.core.ui import print_section, print_success, print_error, print_warning, print_info


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

        for root, _, files in os.walk(self.root_path):
            if 'venv' in root or '.git' in root or '__pycache__' in root:
                continue

            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    module_name = self.get_module_name(full_path)
                    self.files[module_name] = full_path
                    self.modules[full_path] = module_name

                    try:
                        self._parse_file(full_path, module_name)
                    except Exception as e:
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
        # Logic: level is dot count. 
        # For package.sub: 'from .' -> level 1.
        # If current module is 'package.sub.mod', level 1 is 'package.sub'.

        # If current module is a package (has __init__), path includes it. 
        # But get_module_name strips __init__. 
        # Let's assume standard behavior:
        # module 'pkg.mod' -> from . -> 'pkg'
        # module 'pkg' (__init__) -> from . -> 'pkg' (wait, usually relative imports work from package context)

        # A simpler approximation:
        if level > len(parts):
            return None  # Import beyond root

        base = '.'.join(parts[:-level]) if level > 0 else '.'.join(parts)

        if relative_name:
            if base:
                return f"{base}.{relative_name}"
            return relative_name
        return base

    def check_cycles(self) -> List[List[str]]:
        cycles = []
        visited = set()
        path = []
        path_set = set()

        def visit(node):
            if node in path_set:
                # Cycle detected
                cycle = path[path.index(node):] + [node]
                # Canonical form to handle duplicates (rotate to start with min)
                # But here we just want to report it.
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)
            path_set.add(node)

            # Check dependencies
            # Note: dependencies might include external packages. We generally only care about internal cycles.
            # Filter internal only?
            for neighbor in self.dependencies.get(node, []):
                # Simple filter: check if neighbor starts with known prefix or is in our scanned files
                # Doing strict check: must be in scanned files

                # Check direct match
                is_internal = neighbor in self.files

                # Check parent package match (imports often target a parent package)
                if not is_internal:
                    # Try to find if neighbor is a prefix of any scanned file 
                    # (this is slow, maybe optimization needed for large codebases)
                    # Better: check if neighbor acts as a package we scanned
                    # We can use the fact that we constructed module names from root.
                    # If start with same prefix... assume single project check usually.
                    pass

                # Often imports are like 'pyspring.core.configuration'. 
                # If we scanned 'src/pyspring', 'pyspring.core' is internal.
                # However, our module names map might rely on where we started scan.
                # If we start at src, names are 'pyspring.core...'
                # If we start at src/pyspring, names are 'core...' 
                # Ideally user runs from src root so names align.

                real_neighbor = self._find_internal_module(neighbor)
                if real_neighbor:
                    visit(real_neighbor)

            path.pop()
            path_set.remove(node)

    def _find_internal_module(self, import_name: str) -> Optional[str]:
        """
        Check if import_name maps to an internal module.
        Handles case where import is a package (init) or module.
        """
        if import_name in self.files:
            return import_name

        # Provide checking for Package imports that map to __init__
        # get_module_name already strips __init__ so 'pyspring' maps to '.../__init__.py'

        # If import is 'pyspring.core' and we have 'pyspring.core' in files (from __init__), it matches.

        # Sometimes imports are broader than files, e.g. import pyspring
        # We assume if it's in self.files keys, it's internal.
        return None

    def run_check(self) -> bool:
        """Returns True if no cycles found"""
        print_section("Circular Dependency Check")
        self.scan()

        print_info(f"Analyzed {len(self.files)} modules.")

        cycles = []

        # Helper to run DFS from each node
        # We effectively implemented it in check_cycles but need to iterate all nodes

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
            print_success("No circular dependencies found.")
            return True

        print_error(f"Found {len(found_cycles)} circular dependencies:")

        # De-duplicate cycles (A->B->A is same as B->A->B)
        unique_cycles = set()
        count = 0

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
            # Print visually
            print("  " + " ->\n  ".join(cycle))

        return False


def run_check_circular(args):
    path = args.path
    # path default is already handled by argparse (default='.')

    checker = CircularDependencyChecker(path)
    success = checker.run_check()
    if not success:
        sys.exit(1)
