import os


def get_ignore_list(root_path: str = '.') -> set:
    """
    Get a set of directory names to ignore.
    Combines hardcoded framework defaults with user's .gitignore (if present).
    
    Args:
        root_path: Project root path to look for .gitignore
    """
    # 1. Hardcoded Defaults (Framework Baseline)
    # These are safe defaults appropriate for any PySpring project context
    ignore_set = {
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

    # 2. Try to read user's .gitignore
    gitignore_path = os.path.join(root_path, '.gitignore')
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # Normalize gitignore patterns to simple directory names for basic os.walk filtering
                    # Note: .gitignore syntax is complex (e.g. negation !, paths src/foo).
                    # We only extract simple, top-level-like directory names for performance and safety.

                    # Case: "dir/" or "/dir" or "dir"
                    clean_line = line.replace('/', '')  # crude approximation on purpose
                    if '*' not in clean_line and '!' not in clean_line:  # skip globs/negation for now
                        ignore_set.add(clean_line)
        except Exception:
            pass  # Fail silently, fall back to defaults

    return ignore_set
