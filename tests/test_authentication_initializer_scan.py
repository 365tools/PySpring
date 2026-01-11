"""
测试 AuthenticationInitializer 是否能被 IoC 容器扫描到
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_scan_initializer():
    """测试扫描初始化器"""
    print("=" * 60)
    print("🔍 测试 AuthenticationInitializer 扫描")
    print("=" * 60)

    # 1. 检查文件是否存在
    initializer_path = project_root / "src" / "pyspring" / "security" / "auth" / "initializer.py"
    print(f"\n1️⃣ 检查文件是否存在:")
    print(f"   路径: {initializer_path}")
    print(f"   存在: {'✅' if initializer_path.exists() else '❌'}")

    # 2. 尝试直接导入
    print(f"\n2️⃣ 尝试直接导入:")
    try:
        from pyspring.security.authentication.initializer import AuthenticationInitializer
        print(f"   导入: ✅")
        print(f"   类名: {AuthenticationInitializer.__name__}")
        print(f"   模块: {AuthenticationInitializer.__module__}")
        print(f"   基类: {[base.__name__ for base in AuthenticationInitializer.__bases__]}")
    except Exception as e:
        print(f"   导入: ❌ {e}")
        return

    # 3. 检查是否继承正确的接口
    print(f"\n3️⃣ 检查接口继承:")
    from pyspring.core.interfaces.IStartupInitializer import IStartupInitializer
    from pyspring.core.interfaces.ISingleton import ISingletonService
    print(f"   继承 IStartupInitializer: {'✅' if issubclass(AuthenticationInitializer, IStartupInitializer) else '❌'}")
    print(f"   继承 ISingletonService: {'✅' if issubclass(AuthenticationInitializer, ISingletonService) else '❌'}")

    # 4. 测试 IoC 容器扫描
    print(f"\n4️⃣ 测试 IoC 容器扫描:")
    try:
        from pyspring.ioc.manager import AppContainerManager
        ioc_manager = AppContainerManager()

        print(f"   注册服务...")
        ioc_manager.register_all_services()

        print(f"   已注册的服务数: {len(ioc_manager._registered_services)}")

        # 查找 AuthenticationInitializer
        initializer_name = ioc_manager.generate_name(AuthenticationInitializer)
        print(f"   生成的服务名: {initializer_name}")
        print(f"   是否已注册: {'✅' if initializer_name in ioc_manager._registered_services else '❌'}")

        # 尝试获取实例
        if initializer_name in ioc_manager._registered_services:
            try:
                instance = ioc_manager.container.get(initializer_name)
                print(f"   获取实例: ✅")
                print(f"   实例类型: {type(instance).__name__}")
            except Exception as e:
                print(f"   获取实例: ❌ {e}")

        # 列出所有 Initializer
        print(f"\n   所有已注册的 Initializer:")
        for service_name in sorted(ioc_manager._registered_services):
            if 'initializer' in service_name:
                print(f"      - {service_name}")

    except Exception as e:
        print(f"   扫描失败: ❌ {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_scan_initializer()
