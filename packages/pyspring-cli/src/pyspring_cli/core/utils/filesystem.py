import os
from typing import List, Set

DEFAULT_IGNORES = {
    # SCM
    '.git', '.svn', '.hg',
    # Python
    '__pycache__', '.pytest_cache', '.pyspring_cache',
    '.tox', '.nox', '.mypy_cache', '.ruff_cache',
    '*.egg-info', 'dist', 'build', 'wheels',
    # Virtual Envs
    'venv', '.venv', 'env', '.env',
    # IDEs
    '.idea', '.vscode', '.cursor',
    # Web
    'node_modules',
}


def get_ignore_list(root_path: str = '.', extra_ignores: Set[str] = None) -> Set[str]:
    """
    Get a set of directory names to ignore.
    Combines defaults with user's .gitignore (if present).
    
    Args:
        root_path: Project root path to look for .gitignore
        extra_ignores: Additional ignores to add
    """
    ignore_set = DEFAULT_IGNORES.copy()
    if extra_ignores:
        ignore_set.update(extra_ignores)

    # Try to read user's .gitignore
    gitignore_path = os.path.join(root_path, '.gitignore')
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    clean_line = line.replace('/', '')
                    if '*' not in clean_line and '!' not in clean_line:
                        ignore_set.add(clean_line)
        except Exception:
            pass

    return ignore_set


def is_ignored(name: str, ignore_patterns: Set[str]) -> bool:
    """
    Check if a file or directory name matches any ignore pattern.
    Supports basic glob patterns: *, ?
    """
    if name in ignore_patterns:
        return True

    import fnmatch
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(name, pattern):
            return True

    # Also ignore .startswith('.') for hidden files (except current dir)
    if name.startswith('.') and name != '.':
        return True

    return False


def find_files(root_dir: str, extensions: List[str] = None) -> List[str]:
    """
    Recursively find files in a directory, respecting ignore lists.
    :param root_dir: Directory to scan
    :param extensions: List of extensions to include (e.g. ['.py', '.md']). If None, include all.
    """
    found_files = []
    # Always get ignores relative to the directory being scanned, OR current working dir
    # We prefer the root being scanned to catch nested ignore files if needed, 
    # but for simplicity we stick to global ignores + root.
    ignored = get_ignore_list(root_dir)

    abs_root = os.path.abspath(root_dir)

    # If user provided a single file
    if os.path.isfile(abs_root):
        # We still should check if the file itself is ignored, but typically explicit paths override ignores.
        # But let's check basic hidden/ignore rules just in case
        filename = os.path.basename(abs_root)
        if is_ignored(filename, ignored):
            return []
             
        if extensions:
            _, ext = os.path.splitext(abs_root)
            if ext.lower() in extensions:
                return [abs_root]
        else:
            return [abs_root]
        return []

    for root, dirs, files in os.walk(abs_root):
        # Apply ignore filter to dirs in-place to prune traversal
        # We need to filter dirs list directly to stop os.walk from entering them

        # 1. Expand ignore set to patterns check
        dirs_to_keep = []
        for d in dirs:
            if not is_ignored(d, ignored):
                dirs_to_keep.append(d)

        dirs[:] = dirs_to_keep

        for file in files:
            if is_ignored(file, ignored):
                continue
                
            if extensions:
                _, ext = os.path.splitext(file)
                if ext.lower() not in extensions:
                    continue
            found_files.append(os.path.join(root, file))

    return found_files


def find_python_files(root_dir: str) -> List[str]:
    """
    Recursively find all .py files.
    """
    return find_files(root_dir, ['.py'])
