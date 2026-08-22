"""
Token 生成器工厂

根据配置动态创建 Token 生成器实例
"""

from pyspring.core.ioc.context import ApplicationContext
from pyspring.core.log.instance import logger
from pyspring.security.authentication.contracts.token import ITokenGenerator
from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator


class TokenGeneratorFactory:
    """Token 生成器工厂"""

    # 生成器类型映射表
    _generator_registry: dict[str, type[ITokenGenerator]] = {
        "JWT": JWTTokenGenerator,
        "jwt": JWTTokenGenerator,
        # 未来可扩展：
        # "Session": SessionTokenGenerator,
        # "APIKey": APIKeyTokenGenerator,
    }

    @classmethod
    def register_generator_type(cls, generator_type: str, generator_class: type[ITokenGenerator]):
        """
        注册自定义 Token 生成器类型

        Args:
            generator_type: 生成器类型名称
            generator_class: 生成器类
        """
        cls._generator_registry[generator_type] = generator_class
        logger.info(f"[TokenGenFactory] 注册 Token 生成器类型: {generator_type}")

    @classmethod
    def create_generator(cls, generator_type: str = "JWT") -> ITokenGenerator:
        """
        创建 Token 生成器实例

        Args:
            generator_type: 生成器类型（默认 JWT）

        Returns:
            ITokenGenerator: Token 生成器实例

        Raises:
            ValueError: 未知的生成器类型
        """
        if generator_type not in cls._generator_registry:
            logger.warning(f"[TokenGenFactory] 未知的生成器类型: {generator_type}, 使用默认 JWT")
            generator_type = "JWT"

        generator_class = cls._generator_registry[generator_type]

        # 从 IOC 容器获取实例（支持依赖注入）
        try:
            container = ApplicationContext.get_instance()
            generator = container.get_by_type(generator_class)
            logger.info(f"[TokenGenFactory] 创建 Token 生成器: {generator_type}")
            return generator
        except Exception as e:
            logger.error(f"[TokenGenFactory] 创建生成器失败: {e}")
            raise

    @classmethod
    def get_default_generator(cls) -> ITokenGenerator:
        """获取默认的 Token 生成器（JWT）"""
        return cls.create_generator("JWT")
