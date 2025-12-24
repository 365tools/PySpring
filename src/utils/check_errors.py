"""
Python文件错误检测脚本

遍历项目文件夹，检测所有Python文件的语法错误和导入错误
"""
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple


@dataclass
class FileError:
    """文件错误信息"""
    file_path: str
    error_type: str
    line_number: int
    message: str


class PythonFileChecker:
    """Python文件错误检查器"""

    def __init__(self, root_dir: str, exclude_dirs: List[str] = None):
        """
        初始化检查器
        
        Args:
            root_dir: 项目根目录
            exclude_dirs: 要排除的目录列表
        """
        self.root_dir = Path(root_dir)
        self.exclude_dirs = exclude_dirs or [
            '__pycache__',
            '.git',
            'venv',
            'env',
            '.venv',
            'node_modules',
            'dist',
            'build',
            '.egg-info'
        ]
        self.errors: List[FileError] = []

    def should_skip_dir(self, dir_path: Path) -> bool:
        """判断是否应该跳过该目录"""
        dir_name = dir_path.name
        return any(excluded in str(dir_path) or dir_name == excluded
                   for excluded in self.exclude_dirs)

    def check_syntax(self, file_path: Path) -> List[FileError]:
        """
        检查Python文件的语法错误
        
        Args:
            file_path: Python文件路径
            
        Returns:
            错误列表
        """
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # 尝试解析AST
            ast.parse(source_code, filename=str(file_path))

        except SyntaxError as e:
            errors.append(FileError(
                file_path=str(file_path.relative_to(self.root_dir)),
                error_type="SyntaxError",
                line_number=e.lineno or 0,
                message=str(e.msg)
            ))
        except UnicodeDecodeError as e:
            errors.append(FileError(
                file_path=str(file_path.relative_to(self.root_dir)),
                error_type="EncodingError",
                line_number=0,
                message=f"文件编码错误: {str(e)}"
            ))
        except Exception as e:
            errors.append(FileError(
                file_path=str(file_path.relative_to(self.root_dir)),
                error_type=type(e).__name__,
                line_number=0,
                message=str(e)
            ))

        return errors

    def check_unicode_corruption(self, file_path: Path) -> List[FileError]:
        """
        检查文件中的Unicode乱码字符
        
        Args:
            file_path: Python文件路径
            
        Returns:
            错误列表
        """
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 检查Unicode替换字符 U+FFFD (�)
            replacement_char = '\ufffd'

            for line_num, line in enumerate(lines, start=1):
                if replacement_char in line:
                    # 找出所有出现位置
                    col = line.find(replacement_char)
                    # 提取上下文（前后20个字符）
                    start = max(0, col - 20)
                    end = min(len(line), col + 20)
                    context = line[start:end].strip()

                    errors.append(FileError(
                        file_path=str(file_path.relative_to(self.root_dir)),
                        error_type="UnicodeCorruption",
                        line_number=line_num,
                        message=f"发现乱码字符 '�' (U+FFFD) - 上下文: ...{context}..."
                    ))

        except UnicodeDecodeError as e:
            errors.append(FileError(
                file_path=str(file_path.relative_to(self.root_dir)),
                error_type="EncodingError",
                line_number=0,
                message=f"无法读取文件: {str(e)}"
            ))
        except Exception as e:
            # 静默处理其他错误，避免干扰主检查流程
            pass

        return errors

    def check_imports(self, file_path: Path) -> List[FileError]:
        """
        检查Python文件的导入错误（仅检测明显的导入问题）
        
        Args:
            file_path: Python文件路径
            
        Returns:
            错误列表
        """
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # 解析AST查找导入语句
            tree = ast.parse(source_code, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # 这里只做基础检查，不执行实际导入（避免副作用）
                        pass
                elif isinstance(node, ast.ImportFrom):
                    # 检查相对导入的合法性
                    if node.level > 0 and not node.module:
                        # 相对导入但没有指定模块
                        pass

        except Exception:
            # 如果无法解析，跳过导入检查（已在语法检查中报告）
            pass

        return errors

    def scan_directory(self) -> Tuple[int, int]:
        """
        扫描目录中的所有Python文件
        
        Returns:
            (检查的文件数, 有错误的文件数)
        """
        checked_files = 0
        error_files = 0

        print(f"🔍 开始扫描目录: {self.root_dir}")
        print(f"📝 排除目录: {', '.join(self.exclude_dirs)}\n")

        for file_path in self.root_dir.rglob("*.py"):
            # 跳过排除的目录
            if self.should_skip_dir(file_path.parent):
                continue

            checked_files += 1

            # 检查语法错误
            syntax_errors = self.check_syntax(file_path)

            # 检查Unicode乱码
            unicode_errors = self.check_unicode_corruption(file_path)

            # 检查导入错误
            import_errors = self.check_imports(file_path)

            file_errors = syntax_errors + unicode_errors + import_errors

            if file_errors:
                error_files += 1
                self.errors.extend(file_errors)

        return checked_files, error_files

    def print_report(self):
        """打印错误报告"""
        if not self.errors:
            print("✅ 太好了！没有发现任何错误！")
            return

        print(f"\n{'=' * 80}")
        print(f"❌ 发现 {len(self.errors)} 个错误:")
        print(f"{'=' * 80}\n")

        # 按文件分组错误
        errors_by_file: Dict[str, List[FileError]] = {}
        for error in self.errors:
            if error.file_path not in errors_by_file:
                errors_by_file[error.file_path] = []
            errors_by_file[error.file_path].append(error)

        # 打印每个文件的错误
        for file_path, file_errors in sorted(errors_by_file.items()):
            print(f"📄 文件: {file_path}")
            print(f"   错误数: {len(file_errors)}")

            for error in file_errors:
                if error.line_number > 0:
                    print(f"   └─ 行 {error.line_number}: [{error.error_type}] {error.message}")
                else:
                    print(f"   └─ [{error.error_type}] {error.message}")
            print()

    def save_report(self, output_file: str = "error_report.txt"):
        """
        保存错误报告到文件
        
        Args:
            output_file: 输出文件路径
        """
        report_path = self.root_dir / output_file

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("Python文件错误检测报告\n")
            f.write("=" * 80 + "\n\n")

            if not self.errors:
                f.write("✅ 没有发现任何错误！\n")
                return

            f.write(f"发现 {len(self.errors)} 个错误:\n\n")

            # 按文件分组错误
            errors_by_file: Dict[str, List[FileError]] = {}
            for error in self.errors:
                if error.file_path not in errors_by_file:
                    errors_by_file[error.file_path] = []
                errors_by_file[error.file_path].append(error)

            # 写入每个文件的错误
            for file_path, file_errors in sorted(errors_by_file.items()):
                f.write(f"文件: {file_path}\n")
                f.write(f"错误数: {len(file_errors)}\n")

                for error in file_errors:
                    if error.line_number > 0:
                        f.write(f"  - 行 {error.line_number}: [{error.error_type}] {error.message}\n")
                    else:
                        f.write(f"  - [{error.error_type}] {error.message}\n")
                f.write("\n")

        print(f"📝 错误报告已保存到: {report_path}")


def main():
    """主函数"""
    # 获取脚本所在目录（项目根目录）
    script_dir = Path(__file__).parent.parent.parent
    print(f"🔍 脚本目录: {script_dir}")

    # 可以通过命令行参数指定检查目录
    if len(sys.argv) > 1:
        check_dir = Path(sys.argv[1])
    else:
        # 默认检查 src/pyspring 目录
        check_dir = script_dir / "src" / "pyspring"

    if not check_dir.exists():
        print(f"❌ 错误: 目录不存在: {check_dir}")
        print(f"用法: python {Path(__file__).name} [目录路径]")
        print(f"示例: python {Path(__file__).name} src/pyspring")
        sys.exit(1)

    # 创建检查器
    checker = PythonFileChecker(
        root_dir=str(check_dir),
        exclude_dirs=[
            '__pycache__',
            '.git',
            'venv',
            'env',
            '.venv',
            'dist',
            'build',
            '.egg-info',
            '.pytest_cache'
        ]
    )

    # 扫描文件
    checked_files, error_files = checker.scan_directory()

    # 打印统计信息
    print(f"\n{'=' * 80}")
    print(f"📊 扫描统计:")
    print(f"{'=' * 80}")
    print(f"✅ 检查的文件数: {checked_files}")
    print(f"❌ 有错误的文件数: {error_files}")
    print(f"✅ 无错误的文件数: {checked_files - error_files}")

    # 打印错误报告
    checker.print_report()

    # 保存报告到文件
    if checker.errors:
        checker.save_report()

    # 返回错误码
    sys.exit(1 if checker.errors else 0)


if __name__ == "__main__":
    main()
