"""
密码编码器相关接口
"""
from abc import ABC, abstractmethod

from pyspring.ioc.interfaces.core import IManaged


class IPasswordEncoder(IManaged, ABC):
    """
    密码编码器接口
    
    支持用户自定义密码编码算法（BCrypt、Argon2、Pbkdf2等）
    
    示例：
        # 默认实现（BCrypt）
        @Component
        class BCryptPasswordEncoder(IPasswordEncoder):
            def encode(self, raw_password: str) -> str:
                return bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()
            
            def verify(self, raw_password: str, encoded_password: str) -> bool:
                return bcrypt.checkpw(raw_password.encode(), encoded_password.encode())
        
        # 用户DIY（Argon2）
        @Component
        class Argon2PasswordEncoder(IPasswordEncoder):
            def encode(self, raw_password: str) -> str:
                return argon2.hash(raw_password)
            
            def verify(self, raw_password: str, encoded_password: str) -> bool:
                return argon2.verify(encoded_password, raw_password)
    """

    @abstractmethod
    def encode(self, raw_password: str) -> str:
        """
        编码原始密码
        
        Args:
            raw_password: 原始密码（明文）
            
        Returns:
            str: 编码后的密码（哈希值）
        """
        pass

    @abstractmethod
    def verify(self, raw_password: str, encoded_password: str) -> bool:
        """
        验证密码
        
        Args:
            raw_password: 原始密码（明文）
            encoded_password: 已编码的密码（哈希值）
            
        Returns:
            bool: 密码是否匹配
        """
        pass
