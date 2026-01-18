"""
Clean unused imports operations
"""
import ast
import os
from typing import List

from pyspring.cli.core.ui.console import print_success, print_title, print_file_header, print_issue, print_summary


class UnusedImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = {}  # {name: (node, alias_name)}
        self.used_names = set()
        self.has_all = False  # If __all__ is present, we should be careful

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            # Record the definition line/node
            self.imports[name] = node

    def visit_ImportFrom(self, node):
        if node.module == '__future__':
            return  # Keep future imports
        for alias in node.names:
            if alias.name == '*':
                continue
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)

    def visit_Attribute(self, node):
        # We only care about the root name
        # e.g. os.path -> usage of os
        self.visit(node.value)

    def visit_Assign(self, node):
        # Check for __all__
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '__all__':
                self.has_all = True
        self.generic_visit(node)


def get_unused_imports(file_path: str) -> List[int]:
    """
    Return list of line numbers of unused imports.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        tree = ast.parse(code)
    except Exception:
        return []

    visitor = UnusedImportVisitor()
    visitor.visit(tree)

    # Files with __init__.py usually export potential unused imports, skip them to be safe
    # Or if __all__ is defined.
    if visitor.has_all or file_path.endswith('__init__.py'):
        return []

    unused_lines = set()
    for name, node in visitor.imports.items():
        if name not in visitor.used_names:
            unused_lines.add(node.lineno)

    return sorted(list(unused_lines))


def remove_unused_imports_in_file(file_path: str, verbose: bool = False) -> int:
    unused_lines = get_unused_imports(file_path)
    if not unused_lines:
        return 0

    if verbose:
        print_file_header(file_path)
        for line in unused_lines:
            print_issue(str(line), "Removing unused import", file_path, level='info')

    # Read lines
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    removed_count = 0

    # Convert 1-based lineno to 0-based index
    unused_indices = {l - 1 for l in unused_lines}

    for i, line in enumerate(lines):
        if i in unused_indices:
            removed_count += 1
            if not verbose:
                # If not verbose, we didn't print issues above, so maybe we should?
                # But standard 'clean' might be quieter than 'check'.
                pass
        else:
            new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return removed_count

def run_clean_imports(args):
    """
    Walk through directory and remove unused imports.
    Note: 'clean' usually implies action.
    """
    target_dir = os.path.abspath(args.path)
    print_title(f"Cleaning Unused Imports: {target_dir}")

    files_checked = 0
    files_modified = 0
    total_removed = 0

    for root, _, files in os.walk(target_dir):
        if 'venv' in root or '.git' in root: continue

        for file in files:
            if not file.endswith('.py'): continue

            file_path = os.path.join(root, file)
            files_checked += 1

            removed = remove_unused_imports_in_file(file_path, verbose=args.verbose)
            if removed > 0:
                files_modified += 1
                total_removed += removed
                if not args.verbose:
                    print_success(f"Cleaned {removed} imports in {os.path.relpath(file_path)}")

    print_summary(total_removed, files_modified, total_removed, fixable=False)

    if total_removed > 0:
        print()
        print_title("Next Steps")
        print_success("Unused imports removed. Please verify your code:")
        print("  pyspring test")