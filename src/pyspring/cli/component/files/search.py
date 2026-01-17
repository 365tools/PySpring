import os
from typing import List

from pyspring.cli.component.files.ignore import get_ignore_list


def find_files(root_dir: str, extensions: List[str] = None) -> List[str]:
    """
    Recursively find files in a directory, respecting ignore lists.
    :param root_dir: Directory to scan
    :param extensions: List of extensions to include (e.g. ['.py', '.md']). If None, include all.
    """
    found_files = []
    ignored = get_ignore_list(os.getcwd())

    # Navigate one level up if root_dir is not absolute or current
    abs_root = os.path.abspath(root_dir)

    if os.path.isfile(abs_root):
        # Single file check
        if extensions:
            _, ext = os.path.splitext(abs_root)
            if ext.lower() in extensions:
                return [abs_root]
        else:
            return [abs_root]
        return []

    for root, dirs, files in os.walk(abs_root):
        # Filter directories in-place
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
