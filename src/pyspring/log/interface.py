from abc import abstractmethod
from typing import Any, Protocol


class ILoggerService(Protocol):
    """
    日志服务接口
    """

    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> Any:
        """
        记录信息日志
        :param message: 日志信息
        :param args: 可选参数
        :param kwargs: 可选参数
        :return:
        """
        pass

    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> Any:
        """
        记录错误日志
        :param message: 日志信息
        :param args: 可选参数
        :param kwargs: 可选参数
        :return:
        """
        pass

    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> Any:
        """
        记录调试日志
        :param message: 日志信息
        :param args: 可选参数
        :param kwargs: 可选参数
        :return:
        """
        pass

    @abstractmethod
    def warning(self, message: str, *args, **kwargs) -> Any:
        """
        记录警告日志
        :param message: 日志信息
        :param args: 可选参数
        :param kwargs: 可选参数
        :return:
        """
        pass

    @abstractmethod
    def exception(self, message: str, *args, **kwargs) -> Any:
        """
        记录异常日志
        :param message: 日志信息
        :param args: 可选参数
        :param kwargs: 可选参数
        :return:
        """
        pass

    @abstractmethod
    def critical(self, message: str, *args, **kwargs) -> Any:
        """
        记录关键日志
        :param message: 日志信息
        :param args: 可选参数
        :param kwargs: 可选参数
        :return:
        """
        pass

    @abstractmethod
    def log(self, level: int, message: str, *args, **kwargs) -> Any:
        """
        记录自定义日志级别日志
        :param level: 日志级别
        :param message: 日志信息
        :param args: 可选参数
        :param kwargs: 可选参数
        :return:
        """
        pass

    @abstractmethod
    def bind(self, *args, **kwargs) -> Any:
        """
        绑定结构化上下文，返回新的logger/服务实现
        与loguru.logger.bind保持一致的体验
        """
        pass
