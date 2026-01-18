import ast
import os
import sys
from typing import List

from pyspring.cli.core.ui.console import get_terminal_width
from pyspring.cli.core.ui.console import print_warning, print_info, print_success, print_fix, Colors
from .indexer import ProjectIndexer
from .validate import is_module_available
from ..base import BaseChecker
from ..references import scan_file


class ImportResetVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, sys_path: List[str], force: bool = False):
        self.file_path = file_path
        self.sys_path = sys_path or sys.path
        self.force = force
        self.imports_to_remove = []  # List of lines to remove (1-based)
        self.issues = []

    def _should_remove(self, module_name: str, lineno: int) -> bool:
        if not module_name:
            return False

        # Only target pyspring packages
        if not module_name.startswith('pyspring'):
            return False

        # If force mode, we remove ALL pyspring imports
        if self.force:
            return True

        # Otherwise, check if module is valid in current environment
        if is_module_available(module_name, self.sys_path):
            return False

        # It's an invalid pyspring import -> Remove it
        return True

    def visit_Import(self, node):
        # Handle 'import pyspring.xxx'
        for alias in node.names:
            if self._should_remove(alias.name, node.lineno):
                if alias.asname:
                    self.issues.append({
                        'line': node.lineno,
                        'msg': f"Skipping removal of aliased import '{alias.name} as {alias.asname}' (Manual fix required)",
                        'level': 'warning'
                    })
                else:
                    self.imports_to_remove.append(node.lineno)

    def visit_ImportFrom(self, node):
        # Handle 'from pyspring.xxx import yyy'
        if self._should_remove(node.module, node.lineno):
            # Check for aliases in imported names
            has_alias = any(alias.asname for alias in node.names)
            if has_alias:
                self.issues.append({
                    'line': node.lineno,
                    'msg': f"Skipping removal of aliased import from '{node.module}' (Manual fix required)",
                    'level': 'warning'
                })
            else:
                self.imports_to_remove.append(node.lineno)


class ImportResetChecker(BaseChecker):
    @property
    def title(self):
        return "Import Auto-Migration (Reset & Reconstruct)"

    def __init__(self, target_path, force: bool = False):
        super().__init__(target_path, ['.py'])
        self.force = force
        self.sys_path = sys.path.copy()

        # Add current directory to path for resolution check
        cwd = os.getcwd()
        if cwd not in self.sys_path: self.sys_path.insert(0, cwd)

    def check_file(self, file_path: str, fix: bool = False, **kwargs) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            tree = ast.parse("".join(lines), filename=file_path)
        except Exception:
            return False

        visitor = ImportResetVisitor(file_path, self.sys_path, self.force)
        visitor.visit(tree)

        # Report warnings (aliased imports)
        for issue in visitor.issues:
            self.add_issue(file_path, issue['line'], issue['msg'], level=issue['level'])

        if not visitor.imports_to_remove:
            return bool(visitor.issues)

        # Remove lines (reverse order to preserve line numbers)
        lines_to_remove = sorted(list(set(visitor.imports_to_remove)), reverse=True)

        for lineno in lines_to_remove:
            # 0-indexed list vs 1-indexed AST
            idx = lineno - 1
            original_line = lines[idx].strip()

            if fix:
                # Remove the line
                del lines[idx]
                print_fix(file_path, lineno, f"Removed stale import '{original_line}'", action="Reset")
                self.resolved_count += 1
            else:
                self.add_issue(file_path, lineno, f"Stale import detected: '{original_line}' (Run --fix to reset)", level='error')

        if fix and lines_to_remove:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True

        return True


class ReconstructChecker(BaseChecker):
    @property
    def title(self):
        return "Import Reconstruction"

    def __init__(self, target_path):
        super().__init__(target_path, ['.py'])
        self.indexer = ProjectIndexer(os.getcwd())
        self.indexer.build_index()

        # Also index pyspring library if we can find it
        try:
            import pyspring
            if hasattr(pyspring, '__file__'):
                lib_path = os.path.dirname(pyspring.__file__)
                # Avoid re-indexing if we are developing inside pyspring itself
                abs_cwd = os.path.abspath(os.getcwd())
                # If lib_path is NOT inside current working directory, it's an external library
                if not os.path.abspath(lib_path).startswith(abs_cwd):
                    print_info(f"Indexing external library: {lib_path}")
                    self.indexer.index_path(lib_path, prefix="pyspring")
        except ImportError:
            pass

    def check_file(self, file_path: str, fix: bool = False, **kwargs) -> bool:
        # 1. Scan for missing symbols
        unresolved = scan_file(file_path)
        if not unresolved:
            return False

        # Sort unresolved by line number to report issues in order
        unresolved.sort(key=lambda x: x[1])

        # Read file content once
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find insertion point (Safe Docstring Handling)
        insert_idx = 0
        if lines:
            first_line = lines[0].strip()
            # Check for one-line docstring
            if (first_line.startswith('"""') and first_line.endswith('"""') and len(first_line) > 3) or \
                    (first_line.startswith("'''") and first_line.endswith("'''") and len(first_line) > 3):
                insert_idx = 1
            # Check for multi-line docstring
            elif first_line.startswith('"""') or first_line.startswith("'''"):
                marker = first_line[:3]
                for i, line in enumerate(lines):
                    if i == 0: continue
                    if marker in line:
                        insert_idx = i + 1
                        break

        # Or place after the last existing import to keep imports grouped
        last_import_idx = -1
        for i, line in enumerate(lines):
            line_str = line.strip()
            if line_str.startswith('import ') or line_str.startswith('from '):
                last_import_idx = i

        if last_import_idx != -1:
            insert_idx = last_import_idx + 1

        modifications = False

        # Keep track of what we added to avoid duplicates
        current_file_imports = set()
        for line in lines:
            line_str = line.strip()
            if line_str.startswith('import ') or line_str.startswith('from '):
                current_file_imports.add(line_str)

        for name, lineno, _ in unresolved:
            candidates = self.indexer.find_symbol(name)

            # Simple heuristic: exact match only
            if len(candidates) == 1:
                module = candidates[0]
                new_import = f"from {module} import {name}"

                if new_import in current_file_imports:
                    continue

                if fix:
                    lines.insert(insert_idx, new_import + '\n')
                    current_file_imports.add(new_import)
                    modifications = True
                    self.resolved_count += 1
                    print_fix(file_path, lineno, f"Restored import '{new_import}'", action="Link")
                    # Increment index so next import is added AFTER this one
                    insert_idx += 1
                else:
                    self.add_issue(file_path, lineno, f"Missing import for '{name}'. Found candidate: {module}", level='error')
            elif len(candidates) > 1:
                self.add_issue(file_path, lineno, f"Ambiguous symbol '{name}': {candidates} (Manual fix required)", level='warning')
            else:
                pass

        if fix and modifications:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True

        return bool(unresolved)


def run_import_reset(args):
    """
    1. Remove stale pyspring imports
    2. Run ReconstructChecker to find and add missing imports
    """
    target_path = os.path.abspath(args.path)
    force = getattr(args, 'force', False)
    fix = getattr(args, 'fix', False)

    # 1. Safety Check for Force Mode
    if force and fix:
        print_warning("You are using --force with --fix.")
        print(f"This will REMOVE ALL 'pyspring.*' imports in '{target_path}' and attempt to reconstruct them.")
        print("This is a destructive operation.")

        # Interactive confirmation
        response = input(f"{Colors.BOLD}Are you sure you want to continue? [y/N] {Colors.ENDC}")
        if response.lower() != 'y':
            print("Operation cancelled.")
            sys.exit(0)

    # 2. Step 1: Reset (Remove stale imports)
    print_info("Step 1/2: Cleaning stale imports...")
    reset_checker = ImportResetChecker(target_path, force=force)
    reset_checker.run(fix=fix)

    # 3. Step 2: Reconstruct (Scan for missing symbols & Add imports)
    if fix:
        width = get_terminal_width()
        print("\n" + "-" * width + "\n")
        print_info("Step 2/2: Reconstructing imports via symbol analysis...")

        reconstruct_checker = ReconstructChecker(target_path)
        reconstruct_checker.run(fix=True)

        print_success("Migration complete.")
    else:
        width = get_terminal_width()
        print("\n" + "-" * width)
        print_info("To apply migration:")
        print(f"  pyspring check imports-reset {args.path} --fix")