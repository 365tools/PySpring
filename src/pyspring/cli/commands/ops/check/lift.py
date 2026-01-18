"""
Import Lifting Logic
"""
import ast
import os
from collections import defaultdict, deque
from typing import Dict, Set, Optional

from pyspring.cli.core.ui import (
    print_title, print_file_header, print_issue, print_summary,
    print_info, print_warning, print_success
)
from ....core.utils.filesystem import get_ignore_list


class LoadTimeGraphBuilder(ast.NodeVisitor):
    """
    Builds the dependency graph based ONLY on top-level imports.
    """

    def __init__(self, module_name: str, resolve_import_callback):
        self.module_name = module_name
        self.resolve_import = resolve_import_callback
        self.dependencies = set()
        self.scope_depth = 0

    def visit_FunctionDef(self, node):
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_AsyncFunctionDef(self, node):
        self.scope_depth += 1
        self.generic_visit(node)
        self.scope_depth -= 1

    def visit_ClassDef(self, node):
        self.generic_visit(node)

    def visit_Import(self, node):
        if self.scope_depth == 0:
            for alias in node.names:
                target = self.resolve_import(self.module_name, alias.name, 0)
                if target:
                    self.dependencies.add(target)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if self.scope_depth == 0:
            target_module = self.resolve_import(self.module_name, node.module, node.level)
            if target_module:
                self.dependencies.add(target_module)
        self.generic_visit(node)


class LocalImportVisitor(ast.NodeVisitor):
    """
    Finds imports inside functions.
    """

    def __init__(self, module_name: str, resolve_import_callback):
        self.module_name = module_name
        self.resolve_import = resolve_import_callback
        self.local_imports = []  # List[(node, scope_node, target_modules)]
        self.scope_stack = []

    def visit_FunctionDef(self, node):
        self.scope_stack.append(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_AsyncFunctionDef(self, node):
        self.scope_stack.append(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_ClassDef(self, node):
        self.scope_stack.append(node)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Import(self, node):
        if self.is_in_function():
            targets = []
            for alias in node.names:
                t = self.resolve_import(self.module_name, alias.name, 0)
                if t: targets.append(t)
            self.local_imports.append({
                'node': node,
                'scope': self.scope_stack[-1],
                'targets': targets,
                'type': 'import'
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if self.is_in_function():
            target = self.resolve_import(self.module_name, node.module, node.level)
            targets = [target] if target else []
            self.local_imports.append({
                'node': node,
                'scope': self.scope_stack[-1],
                'targets': targets,
                'type': 'from'
            })
        self.generic_visit(node)

    def is_in_function(self):
        # Check if any parent in stack is FunctionDef or AsyncFunctionDef
        for scope in reversed(self.scope_stack):
            if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return True
        return False


class ImportLifter:
    def __init__(self, root_path: str):
        self.root_path = os.path.abspath(root_path)
        self.files: Dict[str, str] = {}  # module -> file_path
        self.graph: Dict[str, Set[str]] = defaultdict(set)

    def get_module_name(self, file_path: str) -> str:
        """Convert file path to dotted module name"""
        rel_path = os.path.relpath(file_path, self.root_path)
        if rel_path.startswith('..'):
            return ""
        name = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
        if name.endswith('.__init__'):
            name = name[:-9]
        return name

    def resolve_import(self, current_module: str, relative_name: Optional[str], level: int) -> Optional[str]:
        if level == 0:
            # Absolute
            return self.find_internal_module(relative_name)

        parts = current_module.split('.')
        if level > len(parts): return None

        base = '.'.join(parts[:-level]) if level > 0 else '.'.join(parts)
        if not relative_name:
            return self.find_internal_module(base)

        target = f"{base}.{relative_name}"
        return self.find_internal_module(target)

    def find_internal_module(self, name: str) -> Optional[str]:
        if not name: return None
        if name in self.files: return name
        return None

    def scan_graph(self):
        """Step 1: Build Load-Time Dependency Graph"""
        print_info(f"Building load-time dependency graph for {self.root_path}...")

        ignore_list = get_ignore_list(os.getcwd())

        # 1. Discover all files
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in ignore_list]
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    mod_name = self.get_module_name(full_path)
                    if mod_name:
                        self.files[mod_name] = full_path

        # 2. Parse for dependencies
        for mod, path in self.files.items():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content, filename=path)
                visitor = LoadTimeGraphBuilder(mod, self.resolve_import)
                visitor.visit(tree)
                self.graph[mod] = visitor.dependencies
            except Exception:
                pass

    def check_reachability(self, start_node: str, target_node: str) -> bool:
        """Check if target_node is reachable from start_node in the graph (BFS)"""
        queue = deque([start_node])
        visited = {start_node}

        while queue:
            current = queue.popleft()
            if current == target_node:
                return True

            for neighbor in self.graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def lift_imports(self, dry_run: bool = True):
        """Step 2 & 3: Find Local Imports and Lift if Safe"""
        print_title("Import Lifting Check")
        self.scan_graph()

        if dry_run:
            print_info("Mode: Dry Run (No changes will be applied)")

        modified_count = 0
        commented_count = 0
        files_modified = 0

        for mod, path in self.files.items():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                visitor = LocalImportVisitor(mod, self.resolve_import)
                visitor.visit(tree)

                if not visitor.local_imports:
                    continue

                lines = content.splitlines()
                # Sort local imports by line number descending to avoid interfering
                visitor.local_imports.sort(key=lambda x: x['node'].lineno, reverse=True)

                file_modified = False
                has_printed_header = False

                added_top_imports = []

                for item in visitor.local_imports:
                    node = item['node']
                    targets = item['targets']

                    is_safe = True
                    reason = ""

                    for target in targets:
                        if target == mod: continue  # Self import?
                        if self.check_reachability(target, mod):
                            is_safe = False
                            reason = f"Cyclic dependency with {target}"
                            break

                    line_idx = node.lineno - 1
                    current_line = lines[line_idx]

                    if "# NOTE: Cannot lift" in current_line or "# Circular" in current_line:
                        continue

                    if not has_printed_header:
                        print_file_header(path)
                        has_printed_header = True

                    indentation = len(current_line) - len(current_line.lstrip())
                    indent_str = current_line[:indentation]

                    # Extract the import string
                    end_line_idx = getattr(node, 'end_lineno', node.lineno) - 1
                    import_lines = lines[line_idx: end_line_idx + 1]
                    import_text = "\n".join(import_lines).strip()

                    if is_safe:
                        if dry_run:
                            print_issue(str(node.lineno), f"Can lift: {import_text}", path, level='info')
                        else:
                            # Remove from local
                            del lines[line_idx: end_line_idx + 1]

                            # Queue for adding to top
                            if import_text not in added_top_imports:
                                added_top_imports.append(import_text)

                            file_modified = True
                            modified_count += 1
                            print_issue(str(node.lineno), f"Lifting: {import_text}", path, level='success')
                    else:
                        if dry_run:
                            print_issue(str(node.lineno), f"Unsafe: {reason}", path, level='error')
                        else:
                            # Add comment
                            if "Cannot lift" not in lines[line_idx - 1] if line_idx > 0 else True:
                                comment = f"{indent_str}# NOTE: Cannot lift due to circular dependency: {reason}"
                                lines.insert(line_idx, comment)
                                file_modified = True
                                commented_count += 1
                                print_issue(str(node.lineno), f"Unsafe to lift: {reason} -> Marked with comment (Manual review needed)", path, level='warning')

                if file_modified and not dry_run:
                    files_modified += 1
                    # Add lifted imports to top
                    insert_pos = 0
                    if len(lines) > 0 and (lines[0].startswith('"""') or lines[0].startswith("'''")):
                        # Skip docstring (naive)
                        for i, line in enumerate(lines):
                            if (line.strip().endswith('"""') or line.strip().endswith("'''")) and i >= insert_pos:
                                insert_pos = i + 1
                                break

                    # Insert collected imports
                    if added_top_imports:
                        lines.insert(insert_pos, "")
                        for imp in reversed(added_top_imports):
                            lines.insert(insert_pos, imp)

                    # Write back
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write("\n".join(lines) + "\n")

            except SyntaxError:
                print_warning(f"Syntax error in {path}")
            except Exception as e:
                print_warning(f"Error processing {path}: {e}")

        print_summary(modified_count + commented_count, files_modified, modified_count, fixable=dry_run)

        if not dry_run and files_modified > 0:
            print()
            print_title("Next Steps")
            print_success("Imports lifted. Please verify the project structure and run tests:")
            print("  pyspring test")


def run_lift_imports(args):
    do_fix = getattr(args, 'fix', False)

    if do_fix:
        user_input = input(f"Are you sure you want to lift safe imports in '{args.target}'? [y/N] ").strip().lower()
        if user_input != 'y':
            print_info("Operation cancelled.")
            return

    lifter = ImportLifter(args.target)
    lifter.lift_imports(dry_run=not do_fix)
    return True
