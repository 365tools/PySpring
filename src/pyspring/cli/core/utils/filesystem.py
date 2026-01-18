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


def find_files(root_dir: str, extensions: List[str] = None) -> List[str]:
    """
    Recursively find files in a directory, respecting ignore lists.
    :param root_dir: Directory to scan
    :param extensions: List of extensions to include (e.g. ['.py', '.md']). If None, include all.
    """
    found_files = []
    ignored = get_ignore_list(os.getcwd())

    abs_root = os.path.abspath(root_dir)

    if os.path.isfile(abs_root):
        if extensions:
            _, ext = os.path.splitext(abs_root)
            if ext.lower() in extensions:
                return [abs_root]
        else:
            return [abs_root]
        return []

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if d not in ignored and not d.startswith('.')]

        for file in files:
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
