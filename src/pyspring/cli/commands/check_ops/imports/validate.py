"""
Validate Imports Command
Combines functionality of scanning for broken imports and resolving them via symbol indexing.
"""
import ast
import os
import sys
from typing import List

from pyspring.cli.component.files.search import find_python_files
from pyspring.cli.core.ui import (
    print_title, print_file_header, print_issue, print_summary,
    print_error
)
from .dynamic import run_check_import as run_dynamic_check
from .indexer import ProjectIndexer
from .static import is_module_available, check_relative_import_exists


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


def run_static_validation(target_path: str, do_fix: bool):
    """Run static validation with auto-fix capability"""
    print_title(f"Import Validation (Static): {target_path}")

    # 1. Build Index (Only needed if we are fixing or suggesting)
    indexer = ProjectIndexer(os.getcwd())
    indexer.build_index()

    # 2. Scan files
    files = find_python_files(target_path)

    # Setup sys path for static resolution
    sys_path = sys.path.copy()
    cwd = os.getcwd()
    if cwd not in sys_path: sys_path.insert(0, cwd)
    src_path = os.path.join(cwd, 'src')
    if os.path.exists(src_path) and src_path not in sys_path: sys_path.insert(0, src_path)

    total_issues = 0
    resolved_count = 0
    files_changed = 0

    for file_path in files:
        # File processing loop ...
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            tree = ast.parse("".join(lines), filename=file_path)
        except SyntaxError as e:
            print_file_header(file_path)
            print_issue(str(e.lineno), f"Syntax Error: {e.msg}", file_path, level='error')
            total_issues += 1
            continue
        except Exception:
            continue

        visitor = BrokenImportVisitor(file_path, sys_path)
        visitor.visit(tree)

        if not visitor.broken_imports:
            continue

        print_file_header(file_path)

        # Sort issues
        visitor.broken_imports.sort(key=lambda x: x['lineno'], reverse=True)

        file_modifications = False

        for issue in visitor.broken_imports:
            total_issues += 1
            lineno = issue['lineno']
            old_mod = issue['module']
            names = issue['names']
            issue_type = issue.get('issue_type', 'missing')

            # --- Handling Bad Practice (src.) ---
            if issue_type == 'bad_practice_src':
                new_mod = old_mod[4:]  # Remove 'src.'

                # Capture indentation
                original_line = lines[lineno - 1]
                indentation = original_line[:len(original_line) - len(original_line.lstrip())]

                # Reconstruct import line for fix
                new_line = ""
                if isinstance(issue['node'], ast.ImportFrom):
                    import_parts = []
                    for name, asname in names:
                        if asname:
                            import_parts.append(f"{name} as {asname}")
                        else:
                            import_parts.append(name)
                    new_line = f"{indentation}from {new_mod} import {', '.join(import_parts)}\n"
                elif isinstance(issue['node'], ast.Import):
                    import_parts = []
                    for name, asname in names:
                        if asname:
                            import_parts.append(f"{new_mod} as {asname}")
                        else:
                            import_parts.append(new_mod)
                    new_line = f"{indentation}import {', '.join(import_parts)}\n"

                msg = f"Bad Layout: '{old_mod}' contains 'src.'"

                if do_fix:
                    if new_line:
                        lines[lineno - 1] = new_line
                        print_issue(str(lineno), f"{msg} -> Fixed to '{new_mod}'", file_path, level='success')
                        resolved_count += 1
                        file_modifications = True
                    else:
                        print_issue(str(lineno), f"{msg} -> Fix failed (could not reconstruct)", file_path, level='error')
                else:
                    print_issue(str(lineno), f"{msg} -> Run --fix to remove prefix", file_path, level='warning')

                continue

            # --- Handling Missing Imports ---
            # Suggestion Logic
            all_resolved = True
            new_modules = set()

            for name, asname in names:
                if name == '*':
                    all_resolved = False  # Cannot auto-resolve import *
                    continue

                candidates = indexer.find_symbol(name)
                # Filter candidates: remove self
                valid_candidates = [c for c in candidates if c != old_mod]

                if len(valid_candidates) == 1:
                    new_modules.add(valid_candidates[0])
                else:
                    all_resolved = False
                    if not valid_candidates:
                        # Report plain error
                        print_issue(str(lineno), f"Module '{old_mod}' not found. Symbol '{name}' also not found in index.", file_path, level='error')
                    else:
                        print_issue(str(lineno), f"Module '{old_mod}' not found. Ambiguous symbol '{name}': {valid_candidates}", file_path, level='warning')

            # Fix Logic
            if all_resolved and len(new_modules) == 1:
                new_mod = list(new_modules)[0]

                # Capture indentation
                original_line = lines[lineno - 1]
                indentation = original_line[:len(original_line) - len(original_line.lstrip())]

                import_parts = []
                for name, asname in names:
                    if asname:
                        import_parts.append(f"{name} as {asname}")
                    else:
                        import_parts.append(name)

                new_line = f"{indentation}from {new_mod} import {', '.join(import_parts)}\n"
                msg = f"Broken: '{old_mod}' -> Suggest: '{new_mod}'"

                if do_fix:
                    lines[lineno - 1] = new_line
                    print_issue(str(lineno), f"{msg} -> Fixed", file_path, level='success')
                    resolved_count += 1
                    file_modifications = True
                else:
                    print_issue(str(lineno), f"{msg} -> Run with --fix to apply", file_path, level='info')
            elif not all_resolved and not new_modules:
                # Issue already reported above
                pass

        if file_modifications:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            files_changed += 1

    print_summary(total_issues, files_changed, resolved_count, fixable=not do_fix)


def run_validate_imports(args):
    """
    Run import validation (Static or Dynamic or Both)
    """
    target_path = os.path.abspath(args.target)
    mode = args.mode
    do_fix = args.fix

    if mode == 'dynamic' and do_fix:
        print_error("Cannot use --fix with --mode dynamic")
        return

    should_run_static = mode in ('static', 'all')
    should_run_dynamic = mode in ('dynamic', 'all')

    if should_run_static:
        run_static_validation(target_path, do_fix)
        if should_run_dynamic:
            print("\n" + "-" * 60 + "\n")

    if should_run_dynamic:
        # Dynamic check delegate
        args.static = False
        run_dynamic_check(args)
