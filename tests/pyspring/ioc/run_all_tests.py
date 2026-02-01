#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IOC测试套件运行器

运行所有IOC相关的测试
"""
import subprocess
import sys
from pathlib import Path

# 测试文件列表
TEST_FILES = [
    "tests/ioc/test_bean_decorator_flexible.py",
    "tests/ioc/test_authentication_ioc.py",
]


def run_test(test_file: str) -> bool:
    """运行单个测试文件"""
    print("\n" + "=" * 80)
    print(f"运行测试: {test_file}")
    print("=" * 80)

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )

        # 打印输出
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # 检查返回码
        if result.returncode != 0:
            print(f"❌ 测试失败: {test_file}")
            return False

        print(f"✅ 测试通过: {test_file}")
        return True

    except subprocess.TimeoutExpired:
        print(f"❌ 测试超时: {test_file}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {test_file} - {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("IOC 测试套件")
    print("=" * 80)

    # 获取tests/ioc目录（当前文件所在目录）
    test_dir = Path(__file__).parent

    results = []
    for test_file in TEST_FILES:
        # 提取文件名
        file_name = Path(test_file).name
        test_path = test_dir / file_name
        if not test_path.exists():
            print(f"⚠️  测试文件不存在: {test_file}")
            results.append(False)
            continue

        success = run_test(str(test_path))
        results.append(success)

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    for i, test_file in enumerate(TEST_FILES):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} - {test_file}")

    print("\n" + "-" * 80)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 80)

    # 返回退出码
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()
