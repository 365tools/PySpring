"""
配置文件查找工具
提供统一的递归搜索配置文件的功能
"""
from pathlib import Path
from typing import Optional



def detect_project_root(start_from: Optional[Path] = None) -> Path:
    """
    检测项目根目录
    
    通过查找项目标志文件（pyproject.toml, setup.py, .git）来确定根目录
    
    Args:
        start_from: 开始搜索的路径（默认为当前工作目录）
        
    Returns:
        项目根目录路径
    """
    if start_from is None:
        try:
            start_from = Path(__file__).resolve().parent
        except NameError:
            start_from = Path.cwd()

    current = start_from
    while current != current.parent:
        if (current / "pyproject.toml").exists() or \
                (current / "setup.py").exists() or \
                (current / ".git").exists():
            return current
        current = current.parent

    return Path.cwd()


def find_config_file(
        filename: str,
        start_path: Optional[Path] = None,
        project_root: Optional[Path] = None
) -> Optional[Path]:
    """
    查找配置文件（仅检查固定位置，不递归搜索）
    
    优先级：
    1. 当前工作目录的 config/ 子目录
    2. 当前工作目录
    3. 项目根目录的 config/ 子目录
    4. 项目根目录
    
    Args:
        filename: 配置文件名（如 'logging.yaml', 'repositories.yaml'）
        start_path: 开始搜索的路径（默认为当前工作目录）
        project_root: 项目根目录（默认为检测到的项目根）
        
    Returns:
        找到的配置文件路径，未找到则返回 None
        
    Examples:
        >>> # 查找日志配置文件
        >>> path = find_config_file('logging.yaml')
        >>> 
        >>> # 查找安全配置文件
        >>> path = find_config_file('security.yaml')
    """
    # 1. 确定起始路径
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)

    # 2. 确定项目根目录
    if project_root is None:
        project_root = detect_project_root(start_path)
    else:
        project_root = Path(project_root)

    # 3. 按优先级查找配置文件
    search_paths = [
        start_path / "config" / filename,  # 1. 当前工作目录的 config/ 子目录
        start_path / filename,  # 2. 当前工作目录
        project_root / "config" / filename,  # 3. 项目根目录的 config/ 子目录
        project_root / filename  # 4. 项目根目录
    ]

    for path in search_paths:
        if path.exists() and path.is_file():
            return path

    return None
