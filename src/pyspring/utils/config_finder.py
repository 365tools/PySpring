"""
配置文件查找工具
提供统一的递归搜索配置文件的功能
"""
from pathlib import Path
from typing import Optional


def find_config_file(
        filename: str,
        start_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
        max_depth: int = 4
) -> Optional[Path]:
    """
    递归查找配置文件
    
    优先级：
    1. 当前工作目录（用户项目）
    2. 项目根目录（框架目录）
    
    Args:
        filename: 配置文件名（如 'logging.yaml', 'repositories.yaml'）
        start_path: 开始搜索的路径（默认为当前工作目录）
        project_root: 项目根目录（默认为检测到的项目根）
        max_depth: 最大搜索深度，防止搜索过深
        
    Returns:
        找到的配置文件路径，未找到则返回 None
        
    Examples:
        >>> # 查找日志配置文件
        >>> path = find_config_file('logging.yaml')
        >>> 
        >>> # 查找安全配置文件
        >>> path = find_config_file('security.yaml')
    """
    if start_path is None:
        start_path = Path.cwd()

    if project_root is None:
        project_root = detect_project_root()

    # 优先搜索当前工作目录（用户项目）
    config_path = _search_config_file(filename, start_path, max_depth)

    # 如果当前工作目录没找到，再搜索框架项目根目录
    if not config_path and start_path != project_root:
        config_path = _search_config_file(filename, project_root, max_depth)

    return config_path


def detect_project_root(start_from: Optional[Path] = None) -> Path:
    """
    检测项目根目录
    
    通过查找项目标志文件（pyproject.toml, setup.py, .git）来确定根目录
    
    Args:
        start_from: 开始查找的路径（默认为当前工作目录）
        
    Returns:
        项目根目录路径
    """
    if start_from is None:
        # 使用当前工作目录而不是框架文件所在目录
        # 这样可以正确检测到用户项目的根目录
        start_from = Path.cwd()
    else:
        start_from = Path(start_from).resolve()

    current = start_from if start_from.is_dir() else start_from.parent

    # 向上查找项目根目录标志文件
    while current != current.parent:
        if (current / "pyproject.toml").exists() or \
                (current / "setup.py").exists() or \
                (current / ".git").exists():
            return current
        current = current.parent

    return Path.cwd()


def _search_config_file(
        filename: str,
        path: Path,
        max_depth: int,
        current_depth: int = 0
) -> Optional[Path]:
    """
    递归搜索配置文件（内部函数）
    
    搜索策略：
    1. 优先查找 config/ 子目录下的文件
    2. 其次查找当前目录下的文件
    3. 递归搜索子目录（跳过常见的大型目录）
    
    Args:
        filename: 配置文件名
        path: 搜索路径
        max_depth: 最大深度
        current_depth: 当前深度
        
    Returns:
        找到的文件路径或 None
    """
    if current_depth > max_depth:
        return None

    # 优先查找当前目录下的 config/ 子目录
    config_dir = path / 'config'
    if config_dir.is_dir():
        config_file = config_dir / filename
        if config_file.exists():
            return config_file

    # 查找当前目录下的配置文件
    config_file = path / filename
    if config_file.exists():
        return config_file

    # 递归搜索子目录（跳过隐藏目录和常见的大型目录）
    try:
        for subdir in path.iterdir():
            if not subdir.is_dir():
                continue

            # 跳过这些目录
            skip_dirs = {
                '__pycache__', '.git', '.venv', 'venv', 'env',
                'node_modules', '.idea', '.vscode', 'build', 'dist',
                '.pytest_cache', '.mypy_cache', '.tox', 'htmlcov',
                'eggs', '.eggs', '*.egg-info', 'logs'
            }
            if subdir.name.startswith('.') or subdir.name in skip_dirs:
                continue

            result = _search_config_file(filename, subdir, max_depth, current_depth + 1)
            if result:
                return result
    except PermissionError:
        pass

    return None
