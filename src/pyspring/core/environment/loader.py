from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv, dotenv_values

from pyspring.log.instance import logger
from ..abstracts.interfaces.ISingleton import ISingletonService


# 实现提供了以下功能:
# 1.加载指定的 .env 文件：
#     EnvConfigLoader 类可以加载指定的环境文件
#     支持覆盖或保留现有的环境变量
# 2.多种加载方式：
#     单个文件加载：load()
#     多个文件加载：load_multiple()
#     自动加载：auto_load() 按照优先级加载多个文件
# 3.读取但不加载：
#     get_env_vars() 可以读取环境变量但不改变系统环境
# 4.便捷函数：
#     提供了方便使用的函数，不需要实例化类
#
# 使用示例：
#     # 加载指定的环境文件
#     loader = EnvConfigLoader(".env.development")
#     loader.load()
#
#     # 或者使用便捷函数
#     load_env_file(".env.production")
#
#     # 自动加载环境配置
#     loaded_files = auto_load_env("dev")
#

class EnvConfigLoader(ISingletonService):
    """
    环境配置加载器（由 IoC 容器管理单例）
    支持加载指定的 .env 文件
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化环境配置加载器

        Args:
            env_file: 环境文件路径，如果为None则使用默认查找逻辑
        """
        self.env_file = env_file

    def load(self, env_file: Optional[str] = None, override: bool = True) -> bool:
        """
        加载指定的环境文件

        Args:
            env_file: 环境文件路径，如果为None则使用实例初始化时的值
            override: 是否覆盖已存在的环境变量

        Returns:
            bool: 加载成功返回True，否则返回False
        """
        file_to_load = env_file or self.env_file

        if not file_to_load:
            logger.warning("⚠️ 未指定环境文件路径")
            return False

        env_path = Path(file_to_load)
        if not env_path.exists():
            logger.warning(f"⚠️ 环境文件不存在: {env_path}")
            return False

        try:
            # 加载环境变量
            load_dotenv(env_path, override=override)
            logger.info(f"✅ 成功加载环境文件: {env_path}")
            return True
        except Exception as e:
            logger.error(f"🚨 加载环境文件失败: {env_path}, 错误: {e}")
            return False

    def load_multiple(self, env_files: List[str], override: bool = True) -> dict:
        """
        按顺序加载多个环境文件

        Args:
            env_files: 环境文件路径列表
            override: 是否覆盖已存在的环境变量

        Returns:
            dict: 每个文件的加载结果
        """
        results = {}
        for env_file in env_files:
            results[env_file] = self.load(env_file, override)
        return results

    def get_env_vars(self, env_file: Optional[str] = None) -> dict:
        """
        获取环境文件中的所有变量（不加载到系统环境）

        Args:
            env_file: 环境文件路径，如果为None则使用实例初始化时的值

        Returns:
            dict: 环境变量键值对
        """
        file_to_read = env_file or self.env_file

        if not file_to_read:
            return {}

        env_path = Path(file_to_read)
        if not env_path.exists():
            return {}

        return dotenv_values(env_path)

    @staticmethod
    def auto_load(environment: str = "dev") -> List[str]:
        """
        自动加载环境配置文件

        Args:
            environment: 环境名称 (dev, prod, test)

        Returns:
            List[str]: 成功加载的文件列表
        """
        project_root = Path(__file__).parent.parent.parent.parent.parent

        # 按优先级顺序尝试加载配置文件
        env_files = [
            project_root / ".env",  # 基础配置 (最低优先级)
            project_root / ".env.local",  # 本地配置 (中等优先级)
            project_root / f".env.{environment}",  # 环境特定配置 (最高优先级)
        ]

        loader = EnvConfigLoader()
        loaded_files = []

        for config_file in env_files:
            if loader.load(str(config_file), override=True):
                loaded_files.append(str(config_file))

        if not loaded_files:
            logger.info("⚙️ 未找到任何配置文件，使用默认配置")

        return loaded_files


# 便捷函数
def load_env_file(file_path: str, override: bool = True) -> bool:
    """
    便捷函数：加载指定的环境文件

    Args:
        file_path: 环境文件路径
        override: 是否覆盖已存在的环境变量

    Returns:
        bool: 加载成功返回True，否则返回False
    """
    loader = EnvConfigLoader()
    return loader.load(file_path, override)


def auto_load_env(environment: str = "dev") -> List[str]:
    """
    便捷函数：自动加载环境配置

    Args:
        environment: 环境名称

    Returns:
        List[str]: 成功加载的文件列表
    """
    return EnvConfigLoader.auto_load(environment)
