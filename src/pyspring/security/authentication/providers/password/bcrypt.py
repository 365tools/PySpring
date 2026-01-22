"""
BCrypt密码编码器（默认实现）
"""
import bcrypt
from pyspring.ioc.annotations.component import Component
from pyspring.security.authentication.contracts.password import IPasswordEncoder


@Component()
class BCryptPasswordEncoder(IPasswordEncoder):
    """
    BCrypt密码编码器（默认实现）
    
    使用BCrypt算法进行密码哈希和验证
    - 成本因子：12（默认）
    - 自动盐值生成
    - 抗彩虹表攻击
    
    示例：
        # IOC自动注入
        encoder = ApplicationContext.get(IPasswordEncoder)
        
        # 编码密码
        hashed = encoder.encode("my_password")
        
        # 验证密码
        is_valid = encoder.verify("my_password", hashed)
    """
    
    def __init__(self):
        """初始化BCrypt编码器"""
        self.rounds = 12
    
    def encode(self, raw_password: str) -> str:
        """
        使用BCrypt编码密码
        
        Args:
            raw_password: 原始密码
            
        Returns:
            str: BCrypt哈希值
        """
        password_bytes = raw_password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify(self, raw_password: str, encoded_password: str) -> bool:
        """
        验证密码是否匹配
        
        Args:
            raw_password: 原始密码
            encoded_password: BCrypt哈希值
            
        Returns:
            bool: 密码是否匹配
        """
        password_bytes = raw_password.encode('utf-8')
        encoded_bytes = encoded_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, encoded_bytes)
