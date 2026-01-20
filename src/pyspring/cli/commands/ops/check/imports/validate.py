"""
Validate Imports Command
Combines functionality of scanning for broken imports and resolving them via symbol indexing.
"""
import ast
import os
import sys
from typing import List

from pyspring.cli.core.ui.console import (
    print_error
)
from pyspring.cli.core.ui.console import print_standard_import_tips, get_terminal_width
from pyspring.cli.core.utils.code import get_indentation, apply_indentation
from .dynamic import run_check_import as run_dynamic_check
from .indexer import ProjectIndexer
from .static import is_module_available, check_relative_import_exists
from ..base import BaseChecker


class BrokenImportVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, sys_path: List[str]):
        self.file_path = file_path
        self.sys_path = sys_path
        self.broken_imports = []

    def visit_ImportFrom(self, node):
        module = node.module or ''
        level = node.level or 0

        # Special Check: Bad Practice 'src.' prefix
        if module.startswith('src.'):
            # Capture aliases
            aliases = [(a.name, a.asname) for a in node.names]
            self.broken_imports.append({
                'lineno': node.lineno,
                'module': module,
                'level': level,
                'names': aliases,
                'node': node,
                'issue_type': 'bad_practice_src'
            })
            return

        is_valid = True
        if level > 0:
            if not check_relative_import_exists(self.file_path, module, level):
                is_valid = False
        else:
            if not module or not is_module_available(module, self.sys_path):
                is_valid = False

        if not is_valid:
            aliases = [(a.name, a.asname) for a in node.names]
            self.broken_imports.append({
                'lineno': node.lineno,
                'module': module,
                'level': level,
                'names': aliases,
                'node': node,
                'issue_type': 'missing'
            })

    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name

            # Special Check: Bad Practice 'src.' prefix
            if module.startswith('src.'):
                self.broken_imports.append({
                    'lineno': node.lineno,
                    'module': module,
                    'level': 0,
                    'names': [(alias.name, alias.asname)],
                    'node': node,
                    'issue_type': 'bad_practice_src'
                })
                continue

            if not is_module_available(module, self.sys_path):
                self.broken_imports.append({
                    'lineno': node.lineno,
                    'module': module,
                    'level': 0,
                    'names': [(alias.name, alias.asname)],
                    'node': node,
                    'issue_type': 'missing'
                })


class StaticImportChecker(BaseChecker):
    @property
    def title(self):
        return "Import Validation (Static)"

    def __init__(self, target_path, sys_path=None):
        super().__init__(target_path, ['.py'])
        self.indexer = None
        self.sys_path = sys_path or sys.path.copy()
        self.issue_count = {'missing': 0, 'bad_practice_src': 0}

        # Setup sys path
        cwd = os.getcwd()
        if cwd not in self.sys_path: self.sys_path.insert(0, cwd)
        src_path = os.path.join(cwd, 'src')
        if os.path.exists(src_path) and src_path not in self.sys_path:
            self.sys_path.insert(0, src_path)

    def pre_check(self, files: List[str], **kwargs):
        # Build index
        self.indexer = ProjectIndexer(os.getcwd())
        self.indexer.build_index()

    def check_file(self, file_path: str, fix: bool = False, **kwargs) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            tree = ast.parse("".join(lines), filename=file_path)
        except SyntaxError as e:
            lineno = e.lineno if e.lineno is not None else 0
            self.add_issue(file_path, lineno, f"Syntax Error: {e.msg}")
            return True
        except Exception:
            return False

        visitor = BrokenImportVisitor(file_path, self.sys_path)
        visitor.visit(tree)

        if not visitor.broken_imports:
            return False

        # Sort issues
        visitor.broken_imports.sort(key=lambda x: x['lineno'], reverse=True)

        file_modifications = False
        issues_found = False

        for issue in visitor.broken_imports:
            issues_found = True
            lineno = issue['lineno']
            old_mod = issue['module']
            names = issue['names']
            issue_type = issue.get('issue_type', 'missing')
            self.issue_count[issue_type] = self.issue_count.get(issue_type, 0) + 1

            # --- Handling Bad Practice (src.) ---
            if issue_type == 'bad_practice_src':
                new_mod = old_mod[4:]  # Remove 'src.'

                new_line = ""
                original_line = lines[lineno - 1]
                indentation = get_indentation(original_line)

                if isinstance(issue['node'], ast.ImportFrom):
                    import_parts = []
                    for name, asname in names:
                        if asname:
                            import_parts.append(f"{name} as {asname}")
                        else:
                            import_parts.append(name)
                    new_line = f"from {new_mod} import {', '.join(import_parts)}\n"
                elif isinstance(issue['node'], ast.Import):
                    import_parts = []
                    for name, asname in names:
                        if asname:
                            import_parts.append(f"{new_mod} as {asname}")
                        else:
                            import_parts.append(new_mod)
                    new_line = f"import {', '.join(import_parts)}\n"

                if fix and new_line:
                    lines[lineno - 1] = apply_indentation([new_line], indentation)[0]
                    self.resolved_count += 1
                    file_modifications = True
                    self.add_issue(file_path, lineno, f"Fixed bad layout: '{old_mod}' -> '{new_mod}'", level='success')
                else:
                    self.add_issue(file_path, lineno, f"Bad Layout: '{old_mod}' contains 'src.' (run --fix to correct)", level='warning')
                continue

            # --- Handling Missing Imports ---
            all_resolved = True
            new_modules = set()
            analysis_errors = []

            for name, asname in names:
                if name == '*':
                    all_resolved = False  # Cannot auto-resolve import *
                    continue

                candidates = self.indexer.find_symbol(name)
                # Filter candidates: remove self
                valid_candidates = [c for c in candidates if c != old_mod]

                if len(valid_candidates) == 1:
                    new_modules.add(valid_candidates[0])
                else:
                    all_resolved = False
                    if not valid_candidates:
                        analysis_errors.append(f"Module '{old_mod}' not found. Symbol '{name}' not found.")
                    else:
                        analysis_errors.append(f"Ambiguous symbol '{name}': {valid_candidates}")

            # Fix Logic
            if all_resolved and len(new_modules) == 1:
                new_mod = list(new_modules)[0]
                original_line = lines[lineno - 1]
                indentation = get_indentation(original_line)
                import_parts = []
                for name, asname in names:
                    if asname:
                        import_parts.append(f"{name} as {asname}")
                    else:
                        import_parts.append(name)
                new_line = f"from {new_mod} import {', '.join(import_parts)}\n"

                if fix:
                    lines[lineno - 1] = apply_indentation([new_line], indentation)[0]
                    self.add_issue(file_path, lineno, f"Auto-fix: '{old_mod}' -> '{new_mod}'", level='success')
                    self.resolved_count += 1
                    file_modifications = True
                else:
                    self.add_issue(file_path, lineno, f"Missing: '{old_mod}' (Suggested: '{new_mod}')", level='warning')

            elif fix:
                # If cannot resolve automatically, inform the user instead of deleting blindy
                # Only report as error/manual fix required
                if analysis_errors:
                    for err in analysis_errors:
                        self.add_issue(file_path, lineno, f"{err} (Manual fix required)", level='error')
                else:
                    # Ambiguous or complex
                    self.add_issue(file_path, lineno, f"Unresolved: '{old_mod}' (Manual fix required)", level='error')

            else:
                # Report Errors
                for err in analysis_errors:
                    self.add_issue(file_path, lineno, err, level='error')
                if not analysis_errors and not all_resolved:
                    self.add_issue(file_path, lineno, f"Cannot verify availability of '{old_mod}'", level='warning')

        if file_modifications:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

        return issues_found

    def post_check(self, files: List[str], **kwargs):
        # Implementation moved to print_tips for correct ordering
        pass

    def print_tips(self):
        missing = self.issue_count.get('missing', 0) > 0
        print_standard_import_tips(missing_imports=missing)



def run_validate_imports(args):
    """
    Run import validation (Static or Dynamic or Both)
    """
    target_path = os.path.abspath(args.target)
    mode = getattr(args, 'mode', 'static')
    do_fix = getattr(args, 'fix', False)

    if mode == 'dynamic' and do_fix:
        print_error("Cannot use --fix with --mode dynamic")
        return

    should_run_static = mode in ('static', 'all')
    should_run_dynamic = mode in ('dynamic', 'all')

    success = True

    if should_run_static:
        checker = StaticImportChecker(target_path)
        if not checker.run(fix=do_fix):
            success = False
        
        if should_run_dynamic:
            width = get_terminal_width()
            print("\n" + "-" * width + "\n")

    if should_run_dynamic:
        # Dynamic check delegate
        args.static = False
        if not run_dynamic_check(args):
            success = False

    return success
