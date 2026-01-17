import os
from typing import List

from pyspring.cli.component.files.ignore import get_ignore_list


def find_python_files(root_dir: str) -> List[str]:
    """
    Recursively find all .py files in a directory, respecting ignore lists.
    """
    py_files = []
    ignored = get_ignore_list(os.getcwd())

    for root, dirs, files in os.walk(root_dir):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in ignored and not d.startswith('.')]

        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))

    return py_files
