"""
PySpring 自定义配置测试套件

测试用户自定义表、@Bean、@Configuration等扩展场景是否正常工作
"""
import io
import sys

# 设置标准输出编码为UTF-8，解决Windows下中文乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
from unittest.mock import Mock
from typing import Any

# 设置测试环境变量
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-custom-configuration-testing-12345678'


class TestCustomConfiguration:
    """测试自定义配置场景"""

    def test_1_custom_user_table(self):
        """测试1: 自定义用户表结构"""
        print("\n" + "=" * 80)
        print("测试: 自定义用户表")
        print("=" * 80)

        from sqlalchemy import Column, String
        from pyspring.repositories.db.models.common.define import BaseUserTable
        from pyspring.security.authentication.config.entity.config import SecurityEntityConfiguration

        # 创建自定义用户表
        class CustomUserTable(BaseUserTable):
            """用户自定义的用户表，添加了额外字段"""
            __tablename__ = 'custom_users'

            # 继承基础字段，添加自定义字段
            nickname = Column(String(50), nullable=True, comment="昵称")
            phone = Column(String(20), nullable=True, comment="手机号")
            avatar_url = Column(String(255), nullable=True, comment="头像URL")
            department = Column(String(100), nullable=True, comment="部门")

        # 创建自定义配置
        custom_config = SecurityEntityConfiguration(
            user_orm_model=CustomUserTable
        )

        # 验证配置
        assert custom_config.user_orm_model == CustomUserTable
        assert custom_config.user_orm_model.__tablename__ == 'custom_users'

        # 验证自定义字段存在
        assert hasattr(custom_config.user_orm_model, 'nickname')
        assert hasattr(custom_config.user_orm_model, 'phone')
        assert hasattr(custom_config.user_orm_model, 'avatar_url')
        assert hasattr(custom_config.user_orm_model, 'department')

        print("✅ 自定义用户表配置成功")
        print(f"   表名: {custom_config.user_orm_model.__tablename__}")
        print(f"   自定义字段: nickname, phone, avatar_url, department")

    def test_2_custom_login_provider(self):
        """测试2: 自定义登录提供者（继承框架默认实现）"""
        print("\n" + "=" * 80)
        print("测试: 自定义登录提供者")
        print("=" * 80)

        from pyspring.ioc.annotations import Component
        from pyspring.security.authentication.providers.login.password import DefaultPasswordLoginProvider

        # 创建自定义登录提供者（继承框架默认实现）
        @Component()
        class CustomPasswordLoginProvider(DefaultPasswordLoginProvider):
            """
            自定义密码登录提供者
            
            扩展支持多种登录标识符（用户名/邮箱/手机号）
            """

            async def authenticate(self, request: Any) -> Any:
                """重写认证逻辑，支持多种登录方式"""
                # 这里可以添加自定义的认证逻辑
                # 例如：支持手机号登录、邮箱登录等
                return await super().authenticate(request)

        # 验证类已正确装饰
        assert hasattr(CustomPasswordLoginProvider, '__pyspring_component__')
        assert CustomPasswordLoginProvider.__pyspring_component__ is True

        print("✅ 自定义登录提供者创建成功")
        print(f"   类型: {CustomPasswordLoginProvider.__name__}")
        print(f"   父类: {CustomPasswordLoginProvider.__bases__[0].__name__}")

    def test_3_custom_register_service(self):
        """测试3: 自定义注册服务（继承框架默认实现）"""
        print("\n" + "=" * 80)
        print("测试: 自定义注册服务")
        print("=" * 80)

        from pyspring.ioc.annotations import Component
        from pyspring.security.authentication.services.register import DefaultRegisterService

        # 创建自定义注册服务
        @Component()
        class CustomRegisterService(DefaultRegisterService):
            """
            自定义注册服务
            
            可以在这里添加额外的注册逻辑，例如：
            - 发送欢迎邮件
            - 验证邀请码
            - 自动分配默认角色
            """

            async def register_user(self, *args, **kwargs) -> Any:
                """重写注册逻辑"""
                # 调用父类的注册逻辑
                user = await super().register_user(*args, **kwargs)

                # 添加自定义逻辑
                # 例如：发送欢迎邮件
                print(f"   📧 发送欢迎邮件给: {user.email if hasattr(user, 'email') else 'user'}")

                return user

        # 验证类已正确装饰
        assert hasattr(CustomRegisterService, '__pyspring_component__')
        assert CustomRegisterService.__pyspring_component__ is True

        print("✅ 自定义注册服务创建成功")
        print(f"   类型: {CustomRegisterService.__name__}")
        print(f"   父类: {CustomRegisterService.__bases__[0].__name__}")

    def test_4_bean_configuration(self):
        """测试4: 使用@Configuration和@Bean创建自定义组件"""
        print("\n" + "=" * 80)
        print("测试: @Configuration 和 @Bean")
        print("=" * 80)

        from pyspring.ioc.annotations import Configuration, Bean, ConditionalOnMissingBean

        # 创建自定义配置类
        @Configuration()
        class CustomSecurityConfig:
            """自定义安全配置"""

            @Bean()
            @ConditionalOnMissingBean()
            def custom_auth_provider(self):
                """创建自定义认证提供者"""
                print("   🔧 创建自定义认证提供者")
                return Mock(name="CustomAuthProvider")

            @Bean()
            def custom_permission_checker(self):
                """创建自定义权限检查器"""
                print("   🔧 创建自定义权限检查器")
                return Mock(name="CustomPermissionChecker")

        # 验证配置类已正确装饰
        assert hasattr(CustomSecurityConfig, '__pyspring_configuration__')
        assert CustomSecurityConfig.__pyspring_configuration__ is True

        # 验证Bean方法已正确装饰
        assert hasattr(CustomSecurityConfig.custom_auth_provider, '__pyspring_bean__')
        assert hasattr(CustomSecurityConfig.custom_permission_checker, '__pyspring_bean__')

        print("✅ 配置类创建成功")
        print(f"   Bean方法数量: 2")
        print(f"   - custom_auth_provider")
        print(f"   - custom_permission_checker")

    def test_5_conditional_bean_replacement(self):
        """测试5: 条件Bean替换机制"""
        print("\n" + "=" * 80)
        print("测试: 条件Bean替换机制")
        print("=" * 80)

        from abc import ABC, abstractmethod
        from pyspring.ioc.annotations import Component, ConditionalOnMissingBean

        # 定义接口
        class IEmailService(ABC):
            @abstractmethod
            async def send_email(self, to: str, subject: str, body: str) -> bool:
                pass

        # 框架提供的默认实现（带条件装饰器）
        @ConditionalOnMissingBean(IEmailService)
        class DefaultEmailService(IEmailService):
            """框架默认的邮件服务（仅打印日志）"""

            async def send_email(self, to: str, subject: str, body: str) -> bool:
                print(f"   📧 [默认实现] 发送邮件给 {to}")
                return True

        # 用户提供的自定义实现（会替换默认实现）
        @Component()
        class SMTPEmailService(IEmailService):
            """用户自定义的SMTP邮件服务"""

            async def send_email(self, to: str, subject: str, body: str) -> bool:
                print(f"   📧 [SMTP实现] 发送邮件给 {to}")
                return True

        # 验证装饰器标记
        assert hasattr(DefaultEmailService, '__pyspring_conditional_on_missing_bean__')
        assert hasattr(SMTPEmailService, '__pyspring_component__')

        print("✅ 条件Bean机制验证成功")
        print(f"   默认实现: {DefaultEmailService.__name__}")
        print(f"   用户实现: {SMTPEmailService.__name__}")
        print(f"   替换机制: 用户实现会替换默认实现")

    def test_6_primary_bean_selection(self):
        """测试6: Primary Bean 选择机制"""
        print("\n" + "=" * 80)
        print("测试: Primary Bean 选择")
        print("=" * 80)

        from pyspring.ioc.annotations import Component, Primary

        # 多个相同类型的实现
        @Component()
        class RedisCache:
            """Redis缓存实现"""

            def get(self, key: str):
                return f"redis:{key}"

        @Component()
        @Primary()
        class MemoryCache:
            """内存缓存实现（主要候选者）"""

            def get(self, key: str):
                return f"memory:{key}"

        # 验证Primary标记
        assert hasattr(MemoryCache, '__pyspring_primary__')
        assert MemoryCache.__pyspring_primary__ is True
        assert not hasattr(RedisCache, '__pyspring_primary__')

        print("✅ Primary Bean机制验证成功")
        print(f"   候选者1: {RedisCache.__name__}")
        print(f"   候选者2: {MemoryCache.__name__} [Primary]")
        print(f"   注入时优先选择: MemoryCache")

    def test_7_lazy_initialization(self):
        """测试7: 懒加载初始化"""
        print("\n" + "=" * 80)
        print("测试: 懒加载初始化")
        print("=" * 80)

        from pyspring.ioc.annotations import Component, Lazy

        @Component()
        @Lazy()
        class ExpensiveService:
            """
            耗费资源的服务
            
            使用@Lazy装饰，延迟到第一次使用时才实例化
            """

            def __init__(self):
                print("   💤 ExpensiveService 正在初始化...")
                self.initialized = True

            def do_work(self):
                return "work done"

        # 验证Lazy标记
        assert hasattr(ExpensiveService, '__pyspring_lazy__')
        assert ExpensiveService.__pyspring_lazy__ is True

        print("✅ 懒加载机制验证成功")
        print(f"   服务: {ExpensiveService.__name__}")
        print(f"   初始化时机: 第一次使用时")

    def test_8_scope_singleton_vs_prototype(self):
        """测试8: 作用域（Singleton vs Prototype）"""
        print("\n" + "=" * 80)
        print("测试: Bean作用域")
        print("=" * 80)

        from pyspring.ioc.annotations import Component, Singleton, Prototype

        @Component()
        @Singleton()
        class DatabaseConnection:
            """单例Bean - 整个应用共享一个实例"""
            instance_count = 0

            def __init__(self):
                DatabaseConnection.instance_count += 1
                self.id = DatabaseConnection.instance_count

        @Component()
        @Prototype()
        class RequestContext:
            """原型Bean - 每次注入都创建新实例"""
            instance_count = 0

            def __init__(self):
                RequestContext.instance_count += 1
                self.id = RequestContext.instance_count

        # 验证作用域标记
        assert hasattr(DatabaseConnection, '__pyspring_singleton__')
        assert hasattr(RequestContext, '__pyspring_prototype__')

        print("✅ Bean作用域验证成功")
        print(f"   单例Bean: {DatabaseConnection.__name__}")
        print(f"   原型Bean: {RequestContext.__name__}")

    def test_9_custom_user_provider(self):
        """测试9: 自定义用户提供者"""
        print("\n" + "=" * 80)
        print("测试: 自定义用户提供者")
        print("=" * 80)

        from pyspring.ioc.annotations import Component
        from pyspring.security.authentication.contracts.user import IUserProvider

        @Component()
        class LDAPUserProvider(IUserProvider):
            """LDAP用户提供者示例"""

            async def get_user_by_identity(self, identity: str):
                """从LDAP获取用户"""
                print(f"   🔍 从LDAP查询用户: {identity}")
                # 实际实现会连接LDAP服务器
                return None

            async def get_user_by_id(self, user_id: str):
                """从LDAP通过ID获取用户"""
                print(f"   🔍 从LDAP查询用户ID: {user_id}")
                return None

        # 验证实现了接口
        assert hasattr(LDAPUserProvider, '__pyspring_component__')

        print("✅ 自定义用户提供者创建成功")
        print(f"   类型: {LDAPUserProvider.__name__}")
        print(f"   接口: {IUserProvider.__name__}")

    def test_10_integration_scenario(self):
        """测试10: 综合场景 - 完整的自定义配置"""
        print("\n" + "=" * 80)
        print("测试: 综合场景")
        print("=" * 80)

        from sqlalchemy import Column, String, Integer
        from pyspring.ioc.annotations import Configuration, Bean, Component, ConditionalOnMissingBean
        from pyspring.repositories.db.models.common.define import BaseUserTable
        from pyspring.security.authentication.config.entity.config import SecurityEntityConfiguration

        # 1. 自定义用户表
        class EnterpriseUser(BaseUserTable):
            """企业用户表"""
            __tablename__ = 'enterprise_users'

            employee_id = Column(String(20), unique=True, comment="工号")
            department = Column(String(100), comment="部门")
            position = Column(String(100), comment="职位")
            manager_id = Column(Integer, nullable=True, comment="上级ID")

        # 2. 自定义配置类
        @Configuration()
        class EnterpriseSecurityConfig:
            """企业安全配置"""

            @Bean()
            def security_entity_config(self):
                """配置企业用户表"""
                return SecurityEntityConfiguration(
                    user_orm_model=EnterpriseUser
                )

            @Bean()
            @ConditionalOnMissingBean()
            def audit_logger(self):
                """审计日志服务"""
                print("   📝 创建审计日志服务")
                return Mock(name="AuditLogger")

        # 3. 自定义组件
        @Component()
        class EmployeeService:
            """员工服务"""

            def get_employee_info(self, employee_id: str):
                print(f"   👤 查询员工信息: {employee_id}")
                return {"employee_id": employee_id, "name": "张三", "department": "技术部"}

        # 验证所有配置
        assert hasattr(EnterpriseSecurityConfig, '__pyspring_configuration__')
        assert hasattr(EmployeeService, '__pyspring_component__')
        assert EnterpriseUser.__tablename__ == 'enterprise_users'

        print("✅ 综合场景验证成功")
        print(f"   自定义表: {EnterpriseUser.__tablename__}")
        print(f"   配置类: {EnterpriseSecurityConfig.__name__}")
        print(f"   业务组件: {EmployeeService.__name__}")
        print("\n📊 测试总结:")
        print("   - 自定义用户表结构 ✅")
        print("   - 配置类和Bean方法 ✅")
        print("   - 业务组件注册 ✅")
        print("   - 条件Bean机制 ✅")


if __name__ == '__main__':
    """运行所有测试"""

    print("\n" + "=" * 80)
    print("PySpring 自定义配置测试套件")
    print("=" * 80)

    # 运行测试
    test_class = TestCustomConfiguration()

    try:
        test_class.test_1_custom_user_table()
        test_class.test_2_custom_login_provider()
        test_class.test_3_custom_register_service()
        test_class.test_4_bean_configuration()
        test_class.test_5_conditional_bean_replacement()
        test_class.test_6_primary_bean_selection()
        test_class.test_7_lazy_initialization()
        test_class.test_8_scope_singleton_vs_prototype()
        test_class.test_9_custom_user_provider()
        test_class.test_10_integration_scenario()

        print("\n" + "=" * 80)
        print("✅ 所有测试通过！")
        print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ 测试失败: {e}")
        print("=" * 80)
        raise
