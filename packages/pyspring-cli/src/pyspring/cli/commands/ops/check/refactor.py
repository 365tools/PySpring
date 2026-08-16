"""
Refactor Imports Checker
"""
import ast
import os
from typing import List, Optional

from pyspring.cli.core.ui.console import print_info

from .base import BaseChecker


class RefactorImportsChecker(BaseChecker):
    def __init__(self, target_path: str, mode: Optional[str] = 'absolute', level: int = 2):
        super().__init__(target_path, ['.py'])
        self.mode = mode
        self.max_dots = level  # Maximum number of dots allowed (1=., 2=.., etc)

        # Stats for analysis
        self.stats = {'absolute': 0, 'relative': 0, 'mixed_files': 0}
        self.current_file_has_absolute = False
        self.current_file_has_relative = False

        # Determine src_root and root_pkg
        self.src_root = self._find_src_root(self.target_path)
        self.root_pkg = self._get_project_root_package(self.src_root)

    @property
    def title(self) -> str:
        if self.mode is None:
            return "Import Style Analysis"
        return f"Import Refactoring ({'To Relative' if self.mode == 'relative' else 'To Absolute'})"

    def _find_src_root(self, path: str) -> str:
        abs_path = os.path.abspath(path)
        parts = abs_path.split(os.sep)
        if 'src' in parts:
            src_idx = parts.index('src')
            return os.sep.join(parts[:src_idx + 1])
        # Fallback to current working directory or path itself if it looks like root
        if os.path.isdir(os.path.join(abs_path, 'src')):
            return os.path.join(abs_path, 'src')
        return abs_path

    def _get_project_root_package(self, src_path: str) -> str:
        """
        Determine the base package name from src path.
        """
        if src_path.endswith('src'):
            try:
                items = [d for d in os.listdir(src_path) if os.path.isdir(os.path.join(src_path, d)) and not d.startswith('.')]
                if 'pyspring' in items:
                    return 'pyspring'
                # If only one directory, assume it is the package
                if len(items) == 1:
                    return items[0]
            except OSError:
                pass
        return 'pyspring'  # Default fallback

    def get_package_of_file(self, file_path: str) -> str:
        """Return the dotted package name containing the file."""
        abs_file = os.path.abspath(file_path)
        dir_path = os.path.dirname(abs_file)

        if not dir_path.startswith(self.src_root):
            return ''

        rel = os.path.relpath(dir_path, self.src_root)
        if rel == '.':
            return ''
        return rel.replace(os.path.sep, '.')

    def to_relative(self, base_pkg: str, target_pkg: str) -> Optional[str]:
        """
        Convert target_pkg to relative format from base_pkg.
        """
        if not base_pkg or not target_pkg:
            return None

        base_parts = base_pkg.split('.')
        target_parts = target_pkg.split('.')

        # Find common prefix
        i = 0
        for b, t in zip(base_parts, target_parts):
            if b == t:
                i += 1
            else:
                break

        # i is number of common parts
        # Steps up needed = len(base) - i
        # steps_up = 0 -> . (1 dot)
        # steps_up = 1 -> .. (2 dots)

        steps_up = len(base_parts) - i
        dots_needed = steps_up + 1

        # Check against max_dots constraint
        if dots_needed > self.max_dots:
            return None

        if steps_up == 0:
            prefix = "."
        else:
            prefix = "." * dots_needed
        suffix = target_parts[i:]
        return prefix + ".".join(suffix)

    def check_file(self, file_path: str, fix: bool = False, **kwargs) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            tree = ast.parse("".join(lines), filename=file_path)
        except (SyntaxError, UnicodeDecodeError):
            return False

        current_pkg = self.get_package_of_file(file_path)

        edits = []
        issues_found = False

        # Reset file specific stats
        self.current_file_has_absolute = False
        self.current_file_has_relative = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module
                level = node.level if node.level is not None else 0

                if module == '__future__':
                    continue

                full_module_name = None

                if level == 0 and module:
                    # Absolute import
                    if module.startswith(self.root_pkg + '.') or module == self.root_pkg:
                        full_module_name = module
                elif level > 0:
                    # Relative import
                    # Resolve to absolute to check validity/necessity
                    curr_parts = current_pkg.split('.') if current_pkg else []

                    if level - 1 > len(curr_parts):
                        continue  # Cannot resolve

                    if level == 1:
                        base = curr_parts
                    else:
                        base = curr_parts[:-(level - 1)]

                    if module:
                        full_module_name = ".".join(base + [module]) if base else module
                    else:
                        full_module_name = ".".join(base)

                if not full_module_name:
                    continue

                # Check if internal
                if not (full_module_name.startswith(self.root_pkg + '.') or full_module_name == self.root_pkg):
                    continue

                # --- Analysis Stats ---
                if level == 0:
                    self.stats['absolute'] += 1
                    self.current_file_has_absolute = True
                else:
                    self.stats['relative'] += 1
                    self.current_file_has_relative = True

                if self.mode is None:
                    continue  # Analysis only, skip refactoring logic

                # Proposed Change
                new_module_part = None

                if self.mode == 'relative':
                    # Try convert to relative (Absolute -> Relative) OR Optimize/Standardize (Relative -> Relative)
                    # Determine desired relative path first
                    rel = self.to_relative(current_pkg, full_module_name)

                    if rel:
                        new_module_part = rel

                        # If original was already relative, we only update if it CHANGED (e.g. standardizing)
                        # OR if we want to enforce level constraints (unlikely, as level constraint prevents conversion TO relative)
                        pass
                    else:
                        # Cannot convert to relative due to constraints (level) or no common root.
                        # If it is currently relative (level > 0), maybe we should convert it BACK to absolute?
                        # If user asks for --to-relative, but this specific import violates level constraint,
                        # should we force it to become absolute?
                        # Probably yes, "Enforce Relative where possible, else Absolute".

                        if level > 0:
                            # It is relative, but violates current constraints (or logic returns None)
                            # Convert to absolute
                            new_module_part = full_module_name

                elif self.mode == 'absolute':
                    if level > 0:
                        # Convert to absolute
                        new_module_part = full_module_name

                if new_module_part:
                    # Check for multi-line limitation
                    if node.lineno != node.end_lineno:
                        # We can't safely regex replace multi-line imports yet
                        continue

                    line_idx = node.lineno - 1
                    old_line = lines[line_idx]

                    # Construction of new line (simple regex-like replacement)
                    new_line = None

                    if self.mode == 'relative':
                        # from full.path import X
                        prefix = f"from {module}"
                        if prefix in old_line:
                            new_line = old_line.replace(prefix, f"from {new_module_part}", 1)

                        # Handle case where we are replacing an existing relative import (from ... import X)
                        if level > 0:
                            dots = "." * level
                            search_frag = f"from {dots}{module}" if module else f"from {dots}"
                            if search_frag in old_line:
                                new_line = old_line.replace(search_frag, f"from {new_module_part}", 1)

                    elif self.mode == 'absolute':
                        # from . import X or from .sub import X
                        dots = "." * level
                        search_frag = f"from {dots}{module}" if module else f"from {dots}"

                        if search_frag in old_line:
                            # Careful replacement
                            # If original is 'from . import', replacement is 'from absolute import'
                            new_line = old_line.replace(search_frag, f"from {new_module_part}", 1)

                    if new_line and new_line != old_line:
                        issue_msg = f"Refactor: {old_line.strip()} -> {new_line.strip()}"

                        if fix:
                            lines[line_idx] = new_line
                            self.record_fix(file_path, node.lineno, f"{issue_msg} -> Fixed")
                            edits.append(True)
                        else:
                            self.add_issue(file_path, node.lineno, issue_msg, level='info')
                        issues_found = True

        # Track mixed files
        if self.current_file_has_absolute and self.current_file_has_relative:
            self.stats['mixed_files'] += 1

        if self.mode is None:
            return False  # No issues reported in analysis mode

        if fix and edits:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            except Exception as e:
                self.add_issue(file_path, 0, f"Error saving file: {e}", level='error')

        return issues_found

    def post_check(self, files: List[str], **kwargs):
        if self.mode is not None:
            return

        print_info(f"Analyzed {self.files_checked_count} file(s).")

        abs_count = self.stats['absolute']
        rel_count = self.stats['relative']
        mixed = self.stats['mixed_files']
        total = abs_count + rel_count

        print("\nImport Style Statistics:")
        print(f"  • Total Internal Imports: {total}")
        print(f"  • Absolute Imports:       {abs_count}")
        print(f"  • Relative Imports:       {rel_count}")
        print(f"  • Files with Mixed Style: {mixed}")

        status = "Mixed"
        if rel_count == 0 and abs_count > 0:
            status = "Pure Absolute"
        elif abs_count == 0 and rel_count > 0:
            status = "Pure Relative"

        print(f"\nCurrent Project Style: {status}")

        print("\n[Suggestions]")
        print("  1. Keep current state (Do nothing)")
        print("  2. Convert to Relative: pyspring check imports-refactor --to-relative")
        print("  3. Convert to Absolute: pyspring check imports-refactor --to-absolute")


def run_check_refactor(args):
    target_path = getattr(args, 'path', '.')

    to_relative = getattr(args, 'to_relative', False)
    to_absolute = getattr(args, 'to_absolute', False)

    mode = None
    if to_relative:
        mode = 'relative'
    elif to_absolute:
        mode = 'absolute'

    level = int(getattr(args, 'level', 2))

    checker = RefactorImportsChecker(target_path, mode=mode, level=level)
    return checker.run(fix=args.fix)
