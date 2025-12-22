"""
PySpring 测试运行器

快速运行所有测试或特定测试套件
"""
import subprocess
import sys
from pathlib import Path


def run_tests(test_type="all"):
    """
    运行测试
    
    Args:
        test_type: 测试类型
            - all: 运行所有测试
            - comprehensive: 综合测试
            - lifecycle: 生命周期测试
            - ioc: IoC 容器测试
            - auto-discover: 自动发现测试
    """
    tests_dir = Path(__file__).parent

    test_files = {
        "all": str(tests_dir),
        "comprehensive": str(tests_dir / "test_comprehensive.py"),
        "lifecycle": str(tests_dir / "test_full_lifecycle.py"),
        "auto-discover": [
            str(tests_dir / "test_auto_discover_handlers.py"),
            str(tests_dir / "test_auto_discover_initializers.py"),
        ],
    }

    target = test_files.get(test_type, test_files["all"])

    if isinstance(target, list):
        for t in target:
            subprocess.run(["pytest", t, "-v", "--tb=short"])
    else:
        subprocess.run(["pytest", target, "-v", "--tb=short"])


if __name__ == "__main__":
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"\n{'=' * 60}")
    print(f"运行测试: {test_type}")
    print(f"{'=' * 60}\n")
    run_tests(test_type)
