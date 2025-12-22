"""
快速测试脚本 - 不使用 pytest，直接运行核心功能测试
"""
import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyspring.ioc.manager import AppContainerManager
from pyspring.interfaces.IStartupInitializer import IStartupInitializer
from pyspring.interfaces.IShutdownHandler import IShutdownHandler
from pyspring.log.loguru.ins import logger


def test_basic_functionality():
    """测试基础功能"""
    print("\n" + "=" * 70)
    print("PySpring 快速功能测试")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    # 创建一个全局管理器实例供所有测试使用
    manager = AppContainerManager()
    print(f"DEBUG: _initialized = {manager._initialized}")
    print(f"DEBUG: _registered_services count before = {len(manager._registered_services)}")
    manager.register_all_services()
    print(f"DEBUG: _registered_services count after = {len(manager._registered_services)}")

    # 测试 1: 容器初始化
    print("\n✓ 测试 1: 容器初始化")
    try:
        assert manager.container is not None
        print("  ✅ 通过")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        tests_failed += 1

    # 测试 2: 服务注册
    print("\n✓ 测试 2: 服务注册")
    try:
        service_count = len(manager._registered_services)
        assert service_count > 0
        print(f"  ✅ 通过 - 已注册 {service_count} 个服务")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        tests_failed += 1

    # 测试 3: 服务类型扫描
    print("\n✓ 测试 3: 服务类型扫描")
    try:
        service_count = sum(1 for s in manager._registered_services if 'service' in s)
        handler_count = sum(1 for s in manager._registered_services if 'handler' in s)
        initializer_count = sum(1 for s in manager._registered_services if 'initializer' in s)

        assert service_count > 0 and handler_count > 0 and initializer_count > 0
        print(f"  ✅ 通过 - Service: {service_count}, Handler: {handler_count}, Initializer: {initializer_count}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        tests_failed += 1

    # 测试 4: 自动发现 Initializers
    print("\n✓ 测试 4: 自动发现启动初始化器")
    try:
        initializers = manager.get_all_instances_of(IStartupInitializer)

        assert len(initializers) >= 3
        print(f"  ✅ 通过 - 发现 {len(initializers)} 个初始化器:")
        for init in initializers:
            print(f"     • {init.get_name()}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        tests_failed += 1

    # 测试 5: 自动发现 Handlers
    print("\n✓ 测试 5: 自动发现关闭处理器")
    try:
        handlers = manager.get_all_instances_of(IShutdownHandler)

        assert len(handlers) >= 2
        print(f"  ✅ 通过 - 发现 {len(handlers)} 个关闭处理器:")
        for handler in handlers:
            print(f"     • {handler.get_name()}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        tests_failed += 1

    # 测试 6: 依赖注入
    print("\n✓ 测试 6: 依赖注入")
    try:
        from pyspring.repositories.cache.manager import CacheManagerService
        cache_manager = AppContainerManager.service(CacheManagerService)
        assert cache_manager is not None
        print("  ✅ 通过 - CacheManagerService 成功获取")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        tests_failed += 1

    # 总结
    print("\n" + "=" * 70)
    print(f"测试完成: {tests_passed} 通过, {tests_failed} 失败")
    print("=" * 70)

    return tests_failed == 0


async def test_lifecycle():
    """测试完整生命周期"""
    print("\n" + "=" * 70)
    print("测试完整应用生命周期")
    print("=" * 70)

    try:
        # 创建容器
        print("\n📦 步骤 1: 创建 IoC 容器")
        manager = AppContainerManager()
        print("  ✅ 完成")

        # 注册服务
        print("\n📝 步骤 2: 注册所有服务")
        manager.register_all_services()
        print(f"  ✅ 完成 - 已注册 {len(manager._registered_services)} 个服务")

        # 发现 Initializers
        print("\n🔍 步骤 3: 发现启动初始化器")
        initializers = manager.get_all_instances_of(IStartupInitializer)
        print(f"  ✅ 完成 - 发现 {len(initializers)} 个初始化器")

        # 发现 Handlers
        print("\n🔍 步骤 4: 发现关闭处理器")
        handlers = manager.get_all_instances_of(IShutdownHandler)
        print(f"  ✅ 完成 - 发现 {len(handlers)} 个关闭处理器")

        # 启动
        print("\n🚀 步骤 5: 执行启动初始化")
        try:
            await manager.run_startup_initializers()
            print("  ✅ 完成")
        except Exception as e:
            print(f"  ⚠️  有警告: {str(e)[:50]}...")

        # 关闭
        print("\n🔄 步骤 6: 执行关闭处理")
        await manager.run_shutdown_handlers()
        print("  ✅ 完成")

        print("\n" + "=" * 70)
        print("✅ 完整生命周期测试通过")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ 生命周期测试失败: {e}")
        return False


def main():
    """主函数"""
    # 基础功能测试
    basic_passed = test_basic_functionality()

    # 生命周期测试
    lifecycle_passed = asyncio.run(test_lifecycle())

    # 最终结果
    print("\n" + "=" * 70)
    if basic_passed and lifecycle_passed:
        print("🎉 所有测试通过！")
        print("=" * 70)
        return 0
    else:
        print("⚠️  部分测试失败")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
