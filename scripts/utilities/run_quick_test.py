"""快速测试脚本"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest",
     "tests/unit/config", "tests/unit/ioc", "tests/integration",
     "-s", "--tb=line", "-q"],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

print("STDOUT:")
print(result.stdout[-2000:])  # 最后 2000 字符
print("\nSTDERR:")
print(result.stderr[-1000:])  # 最后 1000 字符
print(f"\nReturn code: {result.returncode}")
