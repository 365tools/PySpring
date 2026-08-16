"""
BCrypt密码编码器（默认实现）
"""
import bcrypt
from pyspring.core.ioc.annotations import ConditionalOnMissingBean
from pyspring.security.authentication.contracts.password import IPasswordEncoder


@ConditionalOnMissingBean(IPasswordEncoder)
class BCryptPasswordEncoder(IPasswordEncoder):
    """
    BCrypt密码编码器（默认实现）
    
    使用BCrypt算法进行密码哈希和验证
    - 成本因子：12（默认）
    - 自动盐值生成
    - 抗彩虹表攻击
    
    示例：
        # IOC自动注入
        encoder = ApplicationContext.get_by_type(IPasswordEncoder)
        
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
            
        Note:
            BCrypt限制密码最长72字节，超长密码会被自动截断
        """
        password_bytes = raw_password.encode('utf-8')
        # BCrypt限制：密码不能超过72字节
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
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
        try:
            if not encoded_password:
                from pyspring.core.log.instance import logger
                logger.error("密码验证失败: 数据库中的密码为空")
                return False

            # 检查是否是有效的 BCrypt 哈希（应该以 $2b$ 或 $2a$ 开头）
            if not encoded_password.startswith(('$2b$', '$2a$', '$2y$')):
                from pyspring.core.log.instance import logger
                logger.error(f"密码验证失败: 数据库密码不是有效的 BCrypt 格式，当前格式: {encoded_password[:20]}...")
                return False

            password_bytes = raw_password.encode('utf-8')
            # BCrypt限制：密码不能超过72字节
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            encoded_bytes = encoded_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, encoded_bytes)
        except ValueError as e:
            from pyspring.core.log.instance import logger
            logger.error(f"密码验证失败: {e}")
            return False
        except Exception as e:
            from pyspring.core.log.instance import logger
            logger.error(f"密码验证异常: {type(e).__name__}: {e}")
            return False
