from typing import Any

from pyspring.log.instance import logger, LogManager, ILoggerService

# 1. 正常使用 (默认 Loguru)
print("--- Default Logger (Loguru) ---")
logger.info("This is a log from default logger")
logger.bind(user_id="123").info("Structure log with context")


# 2. 定义自定义 Logger 实现
class MySimpleLogger(ILoggerService):
    def info(self, message: str, *args, **kwargs) -> Any:
        print(f"[MyLogger INFO] {message}")

    def error(self, message: str, *args, **kwargs) -> Any:
        print(f"[MyLogger ERROR] {message}")

    def debug(self, message: str, *args, **kwargs) -> Any:
        print(f"[MyLogger DEBUG] {message}")

    def warning(self, message: str, *args, **kwargs) -> Any:
        print(f"[MyLogger WARN] {message}")

    def exception(self, message: str, *args, **kwargs) -> Any:
        print(f"[MyLogger EXCEPTION] {message}")

    def critical(self, message: str, *args, **kwargs) -> Any:
        print(f"[MyLogger CRITICAL] {message}")

    def log(self, level: int, message: str, *args, **kwargs) -> Any:
        print(f"[MyLogger {level}] {message}")

    def bind(self, *args, **kwargs) -> Any:
        print(f"[MyLogger BIND] {kwargs}")
        return self


# 3. 切换实现
print("\n--- Switching Implementation ---")
LogManager.set_provider(MySimpleLogger)

# 4. 再次使用 (通用的 logger 代理会自动转发到新实现)
logger.info("This message is handled by MySimpleLogger")
logger.bind(request_id="abc").info("Chained call")
