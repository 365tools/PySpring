"""
修复Python文件的UTF-8 BOM错误

移除所有Python文件开头的BOM字符（U+FEFF）
"""
from pathlib import Path
from typing import List


class BOMFixer:
    """BOM字符修复器"""

    def __init__(self, root_dir: str):
        """
        初始化修复器
        
        Args:
            root_dir: 项目根目录
        """
        self.root_dir = Path(root_dir)
        self.fixed_files: List[str] = []
        self.failed_files: List[tuple] = []

    def remove_bom(self, file_path: Path) -> bool:
        """
        移除文件的BOM字符
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功移除BOM
        """
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            # 重新写入文件（不带BOM）
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            self.failed_files.append((str(file_path), str(e)))
            return False

    def fix_file(self, file_path: Path) -> bool:
        """
        检查并修复单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否进行了修复
        """
        try:
            # 检查文件是否有BOM
            with open(file_path, 'rb') as f:
                first_bytes = f.read(3)

            # UTF-8 BOM是 EF BB BF
            if first_bytes.startswith(b'\xef\xbb\xbf'):
                if self.remove_bom(file_path):
                    self.fixed_files.append(str(file_path.relative_to(self.root_dir)))
                    return True

            return False

        except Exception as e:
            self.failed_files.append((str(file_path), str(e)))
            return False

    def fix_directory(self, exclude_dirs: List[str] = None) -> None:
        """
        修复目录中的所有Python文件
        
        Args:
            exclude_dirs: 要排除的目录列表
        """
        exclude_dirs = exclude_dirs or [
            '__pycache__',
            '.git',
            'venv',
            'env',
            '.venv',
            'dist',
            'build',
            '.egg-info'
        ]

        print(f"🔍 开始扫描目录: {self.root_dir}")
        print(f"📝 正在修复UTF-8 BOM错误...\n")

        for file_path in self.root_dir.rglob("*.py"):
            # 跳过排除的目录
            if any(excluded in str(file_path) for excluded in exclude_dirs):
                continue

            self.fix_file(file_path)

    def print_report(self) -> None:
        """打印修复报告"""
        print(f"\n{'=' * 80}")
        print("修复报告")
        print(f"{'=' * 80}\n")

        if self.fixed_files:
            print(f"✅ 成功修复 {len(self.fixed_files)} 个文件:")
            for file_path in self.fixed_files:
                print(f"   - {file_path}")
        else:
            print("✅ 没有发现需要修复的文件")

        if self.failed_files:
            print(f"\n❌ 修复失败 {len(self.failed_files)} 个文件:")
            for file_path, error in self.failed_files:
                print(f"   - {file_path}: {error}")

        print(f"\n{'=' * 80}")
        print(f"总计: 修复 {len(self.fixed_files)} 个, 失败 {len(self.failed_files)} 个")
        print(f"{'=' * 80}")


def main():
    """主函数"""
    # 获取脚本所在目录的src/pyspring目录
    script_dir = Path(__file__).parent
    check_dir = script_dir / "src" / "pyspring"

    if not check_dir.exists():
        print(f"❌ 错误: 目录不存在: {check_dir}")
        return

    # 创建修复器
    fixer = BOMFixer(str(check_dir))

    # 修复所有文件
    fixer.fix_directory()

    # 打印报告
    fixer.print_report()


if __name__ == "__main__":
    main()
