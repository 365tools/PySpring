from typing import List


def get_indentation(line: str) -> str:
    """
    Returns the leading whitespace of a string.
    """
    return line[:len(line) - len(line.lstrip())]


def apply_indentation(new_lines: List[str], indentation: str) -> List[str]:
    """
    Applies the given indentation to each line in the list.
    """
    return [f"{indentation}{line.lstrip()}" for line in new_lines]
