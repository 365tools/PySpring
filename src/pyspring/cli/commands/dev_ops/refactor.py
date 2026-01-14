"""
Import Refactoring Ops
"""
import ast
import os
from typing import Optional

from pyspring.cli.core.ui import print_success, print_error, print_info


def get_project_root_package(src_path: str) -> str:
    """
    Determine the base package name from src path.
    e.g. .../src/pyspring -> pyspring
    """
    # Simple heuristic: assume the folder under 'src' is the main package
    # Or strict 'pyspring' for this project? 
    # Let's try to detect.

    # Ensure absolute
    src_path = os.path.abspath(src_path)

    # If src_path endswith 'src', look inside
    if src_path.endswith('src'):
        items = [d for d in os.listdir(src_path) if os.path.isdir(os.path.join(src_path, d)) and not d.startswith('.')]
        if 'pyspring' in items:
            return 'pyspring'
        if len(items) == 1:
            return items[0]

    # Default fallback
    return 'pyspring'


def resolve_module_path(file_path: str, src_root: str, project_package: str) -> Optional[str]:
    """
    Convert file path to dotted module path.
    d:/.../src/pyspring/core/x.py -> pyspring.core.x
    """
    abs_file = os.path.abspath(file_path)
    abs_src = os.path.abspath(src_root)

    if not abs_file.startswith(abs_src):
        return None

    rel = os.path.relpath(abs_file, abs_src)
    # Remove .py
    if rel.endswith('.py'):
        rel = rel[:-3]
    elif rel.endswith('__init__.py'):
        # __init__ is the package itself
        rel = os.path.dirname(rel)

    return rel.replace(os.path.sep, '.')


def calculate_relative_import(current_module: str, target_module: str) -> str:
    """
    Calculate relative import string from current_module to target_module.
    """
    current_parts = current_module.split('.')
    target_parts = target_module.split('.')

    # Find common prefix length
    common_len = 0
    for c, t in zip(current_parts, target_parts):
        if c == t:
            common_len += 1
        else:
            break

    # If no common prefix (unlikely if in same project), defaults to absolute?
    if common_len == 0:
        return target_module

    # Number of steps up
    # current: a.b.c (len 3)
    # target:  a.x.y (len 3)
    # common:  a (len 1)
    # We are in c. need to go up from c (to b), up from b (to a). 
    # Wait.
    # . is current package (a.b) [if file is a/b/__init__.py] or a.b [if file is a/b/c.py]
    # This distinction matters: Is current_module a package or a module?
    # Python 3 treats 'from . import' relative to the package containing the module.

    # Assumption: current_module is the *package* name if __init__, or *module* name if .py
    # Relative imports are resolved relative to `__package__`.
    # If I am in `pyspring.core.utils` (utils.py), my package is `pyspring.core`.
    # If I am in `pyspring.core` (__init__.py), my package is `pyspring.core`.

    # Let's adjust logic: input `current_module` should be the package name.
    pass


def get_package_of_file(file_path: str, src_root: str) -> str:
    """Return the dotted package name containing the file."""
    abs_file = os.path.abspath(file_path)
    dir_path = os.path.dirname(abs_file)
    abs_src = os.path.abspath(src_root)

    rel = os.path.relpath(dir_path, abs_src)
    if rel == '.':
        return ''
    return rel.replace(os.path.sep, '.')


def to_relative(base_pkg: str, target_pkg: str) -> str:
    """
    Convert target_pkg to relative format from base_pkg.
    base_pkg: pyspring.aop.core
    target_pkg: pyspring.utils
    """
    base_parts = base_pkg.split('.') if base_pkg else []
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
    steps_up = len(base_parts) - i

    if steps_up == 0:
        prefix = "."
    else:
        prefix = "." * (steps_up + 1)

    suffix = target_parts[i:]
    return prefix + ".".join(suffix)


def refactor_file(file_path: str, src_root: str, root_pkg: str, mode: str):
    """
    Refactor imports in a single file.
    mode: 'relative' or 'absolute'
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    try:
        tree = ast.parse("".join(lines), filename=file_path)
    except SyntaxError:
        print_error(f"Syntax Error parsing {file_path}. Skipping.")
        return

    # Collect edits: (lineno, new_line_content)
    edits = []

    current_pkg = get_package_of_file(file_path, src_root)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # from X import Y
            module = node.module
            level = node.level if node.level is not None else 0

            # Skip future
            if module == '__future__':
                continue

            # Determine full absolute path of the imported module
            full_module_name = None

            if level == 0 and module:
                # Format: from pyspring.core import X
                # Check if it starts with root_pkg
                if module.startswith(root_pkg + '.') or module == root_pkg:
                    full_module_name = module
            elif level > 0:
                # Format: from .core import X
                # Convert to absolute first to standardize logic
                # logic: take current_pkg, traverse up 'level' times
                curr_parts = current_pkg.split('.')
                if level - 1 > len(curr_parts):
                    # Too many dots up?
                    continue

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

            # Identify if this import is 'internal' to the project
            if not (full_module_name.startswith(root_pkg + '.') or full_module_name == root_pkg):
                continue

            # Now convert to desired mode
            new_module_part = None

            if mode == 'relative':
                # Target: Relative
                if level > 0: continue  # Already relative

                new_module_part = to_relative(current_pkg, full_module_name)

            elif mode == 'absolute':
                # Target: Absolute
                if level == 0: continue  # Already absolute

                new_module_part = full_module_name

            if new_module_part:
                # Reconstruct the line
                # We need to preserve ' import X, Y, Z' part?
                # AST node has 'names'. But reconstructing exact formatting is hard.
                # Regex on the specific line is safer if we know line number.

                # Limitation: Multi-line imports with parentheses are hard to regex simply.
                # Assume single line for MVP or check node.end_lineno

                if node.lineno != node.end_lineno:
                    # Multi-line import - skipping for safety in this version
                    # print_warning(f"Skipping multi-line import at {file_path}:{node.lineno}")
                    continue

                line_idx = node.lineno - 1
                old_line = lines[line_idx]

                # Simple string replacement on the module part
                # from X import Y -> from NEW import Y
                # from . import Y -> from NEW import Y

                if mode == 'relative':
                    # Replacing Absolute with Relative
                    # from pyspring.core import X
                    # Search for 'from pyspring.core'
                    # Be careful with whitespace

                    # Construct search pattern
                    prefix = f"from {module}"
                    if prefix in old_line:
                        new_line = old_line.replace(prefix, f"from {new_module_part}", 1)
                        edits.append((line_idx, new_line))

                elif mode == 'absolute':
                    # Replacing Relative with Absolute
                    # from .core import X  (level 1, module='core')
                    # from .. import X (level 2, module=None)

                    dots = "." * level
                    if module:
                        search_frag = f"from {dots}{module}"
                    else:
                        search_frag = f"from {dots}"

                    # This search is tricky because ' import' follows.
                    # e.g. 'from .. import'

                    # Let's verify presence
                    if search_frag in old_line:
                        # For 'from .. import', we replace 'from ..' with 'from full.path'
                        # But wait, if module is None, new_module_part is 'pyspring.A'
                        # Result: 'from pyspring.A import'

                        # If module is 'core' (from .core import X)
                        # new_module_part is 'pyspring.core'
                        # replace 'from .core' with 'from pyspring.core'

                        new_line = old_line.replace(search_frag, f"from {new_module_part}", 1)
                        edits.append((line_idx, new_line))

    # Apply edits (reverse order to keep indices valid if line count changed? No, line count won't change here)
    if edits:
        print(f"Refactoring {os.path.basename(file_path)}: {len(edits)} changes")
        for idx, new_content in edits:
            lines[idx] = new_content

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)


def refactor_imports(args):
    """
    Entry point for refactor-imports command.
    """
    target_path = os.path.abspath(args.path)
    to_relative_mode = args.to_relative

    # Determine mode
    mode = 'relative' if to_relative_mode else 'absolute'

    # Find Source Root (assuming target is inside src or is src)
    if 'src' in target_path.split(os.sep):
        # find the 'src' folder
        parts = target_path.split(os.sep)
        src_idx = parts.index('src')
        src_root = os.sep.join(parts[:src_idx + 1])
    else:
        # Fallback
        src_root = target_path

    root_pkg = get_project_root_package(src_root)
    print_info(f"Refactoring imports in {target_path}")
    print_info(f"Mode: {'To Relative' if mode == 'relative' else 'To Absolute'}")
    print_info(f"Project Root Package: {root_pkg}")

    confirm = input("This will modify files in place. Continue? [y/N] ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return

    count = 0
    for root, dirs, files in os.walk(target_path):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                refactor_file(full_path, src_root, root_pkg, mode)
                count += 1

    print_success("Refactoring complete.")
