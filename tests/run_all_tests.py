#!/usr/bin/env python3
"""
PySpring 全套测试运行器
统一运行所有测试，包括框架和CLI工具的测试
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("PySpring 全套测试运行器")
    print("=" * 60)
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 定义测试目录
    test_dirs = [
        "tests/pyspring/unit",
        "tests/pyspring/ioc", 
        "tests/pyspring/security",
        "tests/pyspring/config",
        "tests/pyspring_cli/cli"
    ]
    
    results = {}
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"\n🔍 运行 {test_dir} 测试...")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    test_dir, 
                    "-v", 
                    "--tb=short"
                ], cwd=project_root, capture_output=True, text=True)
                
                results[test_dir] = result.returncode == 0
                
                if result.returncode == 0:
                    print(f"✅ {test_dir} - 全部通过")
                else:
                    print(f"❌ {test_dir} - 部分失败")
                    print("STDOUT:", result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
                    print("STDERR:", result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr)
            except Exception as e:
                print(f"💥 {test_dir} - 执行错误: {e}")
                results[test_dir] = False
        else:
            print(f"\n⚠️  {test_dir} - 目录不存在，跳过")
            results[test_dir] = None
    
    # 输出汇总
    print("\n" + "=" * 60)
    print("测试汇总:")
    print("=" * 60)
    
    passed = 0
    total = 0
    
    for test_dir, result in results.items():
        if result is not None:  # 如果目录存在
            total += 1
            if result:
                print(f"✅ {test_dir}")
                passed += 1
            else:
                print(f"❌ {test_dir}")
        else:
            print(f"⚠️  {test_dir} (跳过)")
    
    print(f"\n总计: {passed}/{total} 个测试目录通过")
    
    if passed == total:
        print("🎉 所有测试均通过！")
        return 0
    else:
        print(f"⚠️  {total - passed} 个测试目录存在失败")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())