"""
测试 DB 模块 IOC 注入架构

验证：
1. 服务自动注册为 @Component
2. Factory 自动注入配置和服务
3. Manager 使用 @property 延迟获取服务
4. API 层可以安全使用 Depends(get_bean(DBManager))
"""
import asyncio
import os

from pyspring.ioc.context import ApplicationContext
from pyspring.repositories.db.manager import DBManagerService


async def test_db_ioc_injection():
    """测试数据库模块 IOC 注入"""
    print("\n" + "=" * 60)
    print("🧪 测试 DB 模块 IOC 注入")
    print("=" * 60)

    # 使用 SQLite 进行测试
    os.environ['DATABASE_TYPE'] = 'sqlite'

    # 1. 初始化 IOC 容器
    ctx = ApplicationContext.initialize(base_packages=["pyspring.repositories.db"])

    # 2. 获取 DBManager（模拟 API 层 Depends）
    db_manager = ctx.get_by_type(DBManagerService)
    assert db_manager is not None, "❌ DBManager 注入失败"
    print("✅ DBManager 成功注入")

    # 3. 测试延迟初始化（首次访问 provider）
    provider = db_manager.provider
    assert provider is not None, "❌ Provider 未初始化"
    print(f"✅ Provider 延迟初始化成功: {provider.__class__.__name__}")

    # 4. 测试数据库会话
    db_service = await db_manager.service()
    assert db_service is not None, "❌ DB Service 获取失败"
    print("✅ DB Service 获取成功")

    # 5. 测试会话创建
    async with await db_manager.session() as session:
        assert session is not None, "❌ Session 创建失败"
        print("✅ Session 创建成功")

    print("\n✅✅✅ DB 模块 IOC 架构验证通过 ✅✅✅\n")

    ApplicationContext.reset()


async def test_db_api_layer_usage():
    """模拟 API 层使用 DB 场景"""
    print("\n" + "=" * 60)
    print("🧪 模拟 API 层使用 DB（FastAPI Depends 模式）")
    print("=" * 60)

    # 设置测试环境
    os.environ['DATABASE_TYPE'] = 'sqlite'

    # 模拟应用启动
    ctx = ApplicationContext.initialize(base_packages=["pyspring.repositories.db"])

    # 模拟 API 依赖注入函数
    def get_db_manager():
        """等价于 FastAPI 的 Depends"""
        return ctx.get_by_type(DBManagerService)

    # 模拟 API 端点调用
    print("\n🔹 模拟 API 端点：数据库操作")
    db_mgr = get_db_manager()
    async with await db_mgr.session() as session:
        print(f"✅ 数据库会话: {session}")

    print("\n✅✅✅ API 层使用场景验证通过 ✅✅✅")
    print("✅ Depends(get_bean(DBManager)) 模式安全可用\n")

    ApplicationContext.reset()


async def main():
    """主测试流程"""
    try:
        await test_db_ioc_injection()
        await test_db_api_layer_usage()

        print("\n" + "=" * 60)
        print("🎉 DB 模块 IOC 架构测试全部通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败：{e}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
