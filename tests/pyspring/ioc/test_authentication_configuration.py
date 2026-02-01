"""
测试 AuthenticationConfiguration 的 Bean 注册

验证：
1. @Configuration 类能被正确扫描
2. @Bean 方法能被正确执行
3. authentication_providers Bean 能正确创建
4. 认证提供者能从配置文件正确加载
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pyspring.ioc.context import ApplicationContext
from pyspring.security.authentication.contracts.request_auth import IRequestAuthenticationProvider


async def test_authentication_configuration_scanning():
    """测试 AuthenticationConfiguration 能被扫描和注册"""
    print("\n" + "=" * 80)
    print("Test: AuthenticationConfiguration Bean Registration")
    print("=" * 80)

    # 设置测试环境变量
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-configuration-testing-12345678'
    os.environ['DATABASE_TYPE'] = 'sqlite'
    os.environ['CACHE_TYPE'] = 'memory'

    # 初始化容器，扫描 pyspring.security 包
    ctx = ApplicationContext.initialize(base_packages=[
        "pyspring.security",
        "pyspring.repositories"
    ])

    print("\n1️⃣ 测试: 能否通过Bean名称获取认证提供者列表")
    try:
        # 直接通过Bean名称获取（这是@Bean方法注册的名称）
        providers_list = ctx.get("authentication_providers")

        if providers_list:
            print(f"   ✅ 成功通过Bean名称获取: {len(providers_list)} 个认证提供者")
            for provider in providers_list:
                print(f"      - {provider.__class__.__name__}: {provider.get_name()}")
        else:
            print("   ⚠️  Bean 'authentication_providers' 存在但为空列表")

    except Exception as e:
        print(f"   ❌ 无法获取 'authentication_providers' Bean: {e}")

    print("\n2️⃣ 测试: 使用 get_all_instances_of 获取（旧方式，预期失败）")
    try:
        # 尝试获取认证提供者列表（这是 @Bean 方法返回的 List）
        providers = ctx.container.get_all_instances_of(IRequestAuthenticationProvider)

        print(f"   ✅ 成功获取认证提供者: {len(providers)} 个")
        for provider in providers:
            print(f"      - {provider.__class__.__name__}")

        if len(providers) == 0:
            print("   ℹ️  说明: get_all_instances_of 无法找到@Bean返回的List")
            print("   解决方案: 直接使用 ctx.get('authentication_providers')")

    except Exception as e:
        print(f"   ❌ 获取认证提供者失败: {e}")

    print("\n3️⃣ 测试: 检查容器中的所有Bean")
    all_beans = ctx.container.registry.all_names()
    print(f"   容器中共有 {len(all_beans)} 个Bean")

    # 查找与认证相关的Bean
    auth_beans = [name for name in all_beans if 'auth' in name.lower() or 'token' in name.lower()]
    if auth_beans:
        print(f"   认证相关的Bean ({len(auth_beans)} 个):")
        for bean_name in sorted(auth_beans)[:10]:  # 只显示前10个
            print(f"      - {bean_name}")
    else:
        print("   ⚠️  没有找到认证相关的Bean")

    print("\n4️⃣ 测试: 检查配置类是否被注册")
    try:
        from pyspring.security.authentication.config.auto_config import AuthenticationConfiguration
        config_instance = ctx.get_by_type(AuthenticationConfiguration)
        if config_instance:
            print(f"   ✅ AuthenticationConfiguration 已注册: {config_instance.__class__.__name__}")
        else:
            print("   ❌ AuthenticationConfiguration 未注册")
    except Exception as e:
        print(f"   ❌ 获取 AuthenticationConfiguration 失败: {e}")

    print("\n5️⃣ 测试: 检查 SecurityConfigManager")
    try:
        from pyspring.security.core.config.loader import SecurityConfigManager
        config_mgr = ctx.get_by_type(SecurityConfigManager)
        if config_mgr:
            print(f"   ✅ SecurityConfigManager 已注册")

            # 检查配置内容
            providers_config = config_mgr.get_providers_config()
            print(f"   配置中定义的认证提供者: {len(providers_config)} 个")
            for prov_conf in providers_config:
                print(f"      - {prov_conf.get('name')} ({prov_conf.get('type')})")
        else:
            print("   ❌ SecurityConfigManager 未注册")
    except Exception as e:
        print(f"   ❌ 检查 SecurityConfigManager 失败: {e}")

    print("\n" + "=" * 80)
    ApplicationContext.reset()


async def test_authentication_providers_manual_creation():
    """测试手动创建认证提供者（模拟Bean方法的执行）"""
    print("\n" + "=" * 80)
    print("Test: Manual Authentication Provider Creation")
    print("=" * 80)

    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-manual-12345678'
    os.environ['DATABASE_TYPE'] = 'sqlite'
    os.environ['CACHE_TYPE'] = 'memory'

    ctx = ApplicationContext.initialize(base_packages=[
        "pyspring.security",
        "pyspring.repositories"
    ])

    print("\n手动调用工厂方法创建认证提供者...")
    try:
        from pyspring.security.authentication.factories.auth_provider.factory import AuthProviderFactory
        from pyspring.security.core.config.loader import SecurityConfigManager
        from pyspring.security.authentication.contracts.token import ITokenService

        # 从容器获取依赖（模拟Bean方法的依赖注入）
        config_manager = ctx.get_by_type(SecurityConfigManager)
        token_service = ctx.get_by_type(ITokenService)

        # 这就是 @Bean 方法内部做的事情
        providers = AuthProviderFactory.create_providers_from_config(
            token_manager=token_service,
            config_manager=config_manager
        )

        print(f"✅ 工厂方法成功创建了 {len(providers)} 个认证提供者")
        for provider in providers:
            print(f"   - {provider.__class__.__name__}: {provider.get_name()}")

        if len(providers) == 0:
            print("\n⚠️  工厂方法返回空列表，可能原因:")
            print("   1. security.yaml 中 authentication.providers 为空")
            print("   2. 提供者创建过程中发生异常")
            print("   3. SecurityConfigManager 未正确加载配置")

    except Exception as e:
        print(f"❌ 工厂方法执行失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    ApplicationContext.reset()


async def main():
    """运行所有测试"""
    try:
        await test_authentication_configuration_scanning()
        await test_authentication_providers_manual_creation()

        print("\n" + "=" * 80)
        print("测试总结:")
        print("  如果看到 '没有找到任何认证提供者'，请检查:")
        print("  1. src/pyspring/config/defaults/security.yaml 中是否定义了 providers")
        print("  2. AuthenticationConfiguration 是否被正确扫描")
        print("  3. 查看上方的调试日志，特别是 [Factory] 开头的日志")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
