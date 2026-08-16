"""
Circular Dependency Checker using AST
"""
import ast
import os
from collections import defaultdict
from typing import Dict, List, Optional, Set

from pyspring.cli.core.ui.console import print_info, print_title

from .base import BaseChecker


class CircularChecker(BaseChecker):
    def __init__(self, target_path: str):
        super().__init__(target_path, ['.py'])

        project_root = os.getcwd()
        self.root_path = project_root
        # Smart detection for source root
        self.package_root = self.target_path
        if self.target_path == project_root:
            src_path = os.path.join(project_root, 'src')
            if os.path.exists(src_path):
                self.package_root = src_path

        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.files: Dict[str, str] = {}  # module -> file_path
        self.modules: Dict[str, str] = {}  # file_path -> module

    @property
    def title(self) -> str:
        return "Circular Dependency Check"

    def check_file(self, file_path: str, fix: bool = False, **kwargs) -> bool:
        module_name = self.get_module_name(file_path)
        self.files[module_name] = file_path
        self.modules[file_path] = module_name
        try:
            self._parse_file(file_path, module_name)
        except Exception:
            return False
        return False

    def post_check(self, files: List[str], **kwargs):
        print_info(f"Analyzed {len(self.files)} modules. Checking for cycles...")

        cycles = self._find_cycles()

        unique_cycles = set()
        count = 0

        for cycle in cycles:
            # Normalize for deduplication
            min_node = min(cycle[:-1])
            start_idx = cycle.index(min_node)
            normalized = tuple(cycle[start_idx:-1] + cycle[:start_idx] + [min_node])

            if normalized in unique_cycles:
                continue
            unique_cycles.add(normalized)
            count += 1

            # Format message
            msg = "Cycle Detected:\n"
            for i, mod in enumerate(cycle):
                prefix = "  "
                if i > 0: prefix = "  ↓ "
                msg += f"{prefix}{mod}\n"

            # Attribute to the first file in the cycle for reporting
            first_file = self.files.get(cycle[0], files[0])
            self.add_issue(first_file, 0, msg, level='error')
            self.files_with_issues_count += 1

    def get_module_name(self, file_path: str) -> str:
        """Convert file path to dotted module name"""
        rel_path = os.path.relpath(file_path, self.package_root)
        if rel_path.startswith('..'):
            rel_path = os.path.relpath(file_path, self.root_path)

        name = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
        if name.endswith('.__init__'):
            name = name[:-9]
        return name

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
                target: Optional[str] = None
                if node.module:
                    if node.level == 0:
                        target = node.module
                    else:
                        target = self._resolve_relative_import(current_module, node.module, node.level)
                    if target and isinstance(target, str):
                        self.dependencies[current_module].add(target)
                else:
                    target = self._resolve_relative_import(current_module, None, node.level)
                    if target and isinstance(target, str):
                        for alias in node.names:
                            self.dependencies[current_module].add(f"{target}.{alias.name}")

    def _resolve_relative_import(self, current_module: str, relative_name: Optional[str], level: int) -> Optional[str]:
        parts = current_module.split('.')
        if level > len(parts):
            return None
        base_parts = parts[:-level] if level > 0 else parts
        base = ".".join(base_parts)
        if relative_name:
            if base:
                return f"{base}.{relative_name}"
            return relative_name
        return base

    def _find_internal_module(self, import_name: str) -> Optional[str]:
        if import_name in self.files:
            return import_name
        return None

    def _find_cycles(self) -> List[List[str]]:
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

        for node in sorted(self.files.keys()):
            dfs(node)

        return found_cycles


def run_check_circular(args):
    target = getattr(args, 'path', '.')
    checker = CircularChecker(target)
    success = checker.run()

    if not success:
        print()
        print_title("Next Steps")
        print_info("To resolve circular dependencies:")
        print("  1. Refactor common logic into a separate module")
        print("  2. Move imports inside functions/methods (delayed import)")
        # sys.exit(1) removed for check --all compatibility

    return success
