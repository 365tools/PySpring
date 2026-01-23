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
    3. 不再递归搜索子目录（避免性能问题）
    
    Args:
        filename: 配置文件名
        path: 搜索路径
        max_depth: 最大深度（已废弃，保留以兼容）
        current_depth: 当前深度（已废弃，保留以兼容）
        
    Returns:
        找到的文件路径或 None
    """
    # 0. 基础检查
    if not path.exists() or not path.is_dir():
        return None

    # 1. 优先检查 config/ 子目录下有没有该文件
    config_dir_file = path / 'config' / filename
    if config_dir_file.exists():
        return config_dir_file

    # 2. 检查当前目录下有没有
    curr_file = path / filename
    if curr_file.exists():
        return curr_file

    # 3. 不再递归搜索子目录，避免在大型项目中性能问题
    return None


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
        max_depth: 最大搜索深度（已废弃，保留以兼容）
        
    Returns:
        找到的配置文件路径，未找到则返回 None
        
    Examples:
        >>> # 查找日志配置文件
        >>> path = find_config_file('logging.yaml')
        >>> 
        >>> # 查找安全配置文件
        >>> path = find_config_file('security.yaml')
    """
