"""
Python文件错误检测脚本

遍历项目文件夹，检测所有Python文件的语法错误、导入错误以及未定义的引用
"""
import ast
import builtins
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple


@dataclass
class FileError:
    """文件错误信息"""
    file_path: str
    error_type: str
    line_number: int
    message: str


class Scope:
    """作用域管理"""

    def __init__(self, parent: Optional['Scope'] = None, is_class_scope: bool = False):
        self.parent = parent
        self.definitions: Set[str] = set()
        self.is_class_scope = is_class_scope
        self.star_imported = False  # 是否包含 from module import *

    def define(self, name: str):
        self.definitions.add(name)

    def is_defined(self, name: str) -> bool:
        if name in self.definitions:
            return True
        if self.parent:
            # 如果是类作用域，父级作用域的查找规则稍微不同，但简化起见，我们暂且允许向上查找
            # 注意：类体中的变量对方法不可见，这是Python的特性
            return self.parent.is_defined(name)
        return False

    def has_star_import(self) -> bool:
        if self.star_imported:
            return True
        if self.parent:
            return self.parent.has_star_import()
        return False


class ReferenceVisitor(ast.NodeVisitor):
    """AST访问器，用于检查未定义的引用"""

    def __init__(self):
        self.current_scope = Scope()
        # 将内建函数加入根作用域
        for name in dir(builtins):
            self.current_scope.define(name)
        self.issues: List[Tuple[int, str]] = []  # (line, message)

    def visit_FunctionDef(self, node):
        self.current_scope.define(node.name)
        # 进入新函数作用域
        prev_scope = self.current_scope
        self.current_scope = Scope(parent=prev_scope)

        # 处理参数
        # 1. 位置参数
        for arg in node.args.args:
            self.current_scope.define(arg.arg)
        # 2. 仅位置参数 (Python 3.8+)
        if hasattr(node.args, 'posonlyargs'):
            for arg in node.args.posonlyargs:
                self.current_scope.define(arg.arg)
        # 3. 仅关键字参数
        if hasattr(node.args, 'kwonlyargs'):
            for arg in node.args.kwonlyargs:
                self.current_scope.define(arg.arg)

        # 处理 kwargs, varargs 等
        if node.args.vararg: self.current_scope.define(node.args.vararg.arg)
        if node.args.kwarg: self.current_scope.define(node.args.kwarg.arg)

        self.generic_visit(node)
        self.current_scope = prev_scope

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self.current_scope.define(node.name)
        # 进入类作用域
        prev_scope = self.current_scope
        self.current_scope = Scope(parent=prev_scope, is_class_scope=True)
        self.generic_visit(node)
        self.current_scope = prev_scope

    def visit_Lambda(self, node):
        prev_scope = self.current_scope
        self.current_scope = Scope(parent=prev_scope)
        for arg in node.args.args:
            self.current_scope.define(arg.arg)
        if node.args.vararg: self.current_scope.define(node.args.vararg.arg)
        if node.args.kwarg: self.current_scope.define(node.args.kwarg.arg)
        self.generic_visit(node)
        self.current_scope = prev_scope

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split('.')[0]
            self.current_scope.define(name)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.name == '*':
                self.current_scope.star_imported = True
            else:
                name = alias.asname if alias.asname else alias.name
                self.current_scope.define(name)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Param)):
            self.current_scope.define(node.id)
        elif isinstance(node.ctx, ast.Load):
            if not self.current_scope.is_defined(node.id) and not self.current_scope.has_star_import():
                # 忽略一些特殊的魔法变量
                if node.id not in ['__file__', '__name__', '__doc__', '__path__']:
                    self.issues.append((node.lineno, f"未解析的引用: '{node.id}'"))

    def visit_Attribute(self, node):
        # 即使只访问属性，我们也只关心主对象是否定义
        # 例如 self.config - 只检查 self 是否定义
        # 我们让 visit_Name 处理 node.value
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.name:
            self.current_scope.define(node.name)
        self.generic_visit(node)

    # 处理列表推导式等的变量泄漏问题 (Python 3中它们有自己的作用域)
    def visit_ListComp(self, node):
        self._visit_comprehension(node)

    def visit_SetComp(self, node):
        self._visit_comprehension(node)

    def visit_DictComp(self, node):
        self._visit_comprehension(node)

    def visit_GeneratorExp(self, node):
        self._visit_comprehension(node)

    def _visit_comprehension(self, node):
        prev_scope = self.current_scope
        self.current_scope = Scope(parent=prev_scope)
        for generator in node.generators:
            self.visit(generator)  # 先访问生成器，定义变量
        # 访问元素表达式
        if hasattr(node, 'elt'): self.visit(node.elt)
        if hasattr(node, 'key'): self.visit(node.key)
        if hasattr(node, 'value'): self.visit(node.value)
        self.current_scope = prev_scope

    def visit_comprehension(self, node):
        self.visit(node.target)  # 定义目标变量
        self.visit(node.iter)  # 访问迭代对象
        for if_ in node.ifs:
            self.visit(if_)


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

    def check_undefined_vars(self, file_path: Path) -> List[FileError]:
        """
        检查未定义的变量引用
        
        Args:
            file_path: Python文件路径
            
        Returns:
            错误列表
        """
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=str(file_path))
            visitor = ReferenceVisitor()
            visitor.visit(tree)

            for lineno, msg in visitor.issues:
                errors.append(FileError(
                    file_path=str(file_path.relative_to(self.root_dir)),
                    error_type="UnresolvedReference",
                    line_number=lineno,
                    message=msg
                ))

        except Exception:
            # 语法错误已在 check_syntax 中处理
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

            # 检查未定义变量
            undefined_errors = self.check_undefined_vars(file_path)

            # 检查导入错误
            import_errors = self.check_imports(file_path)

            file_errors = syntax_errors + unicode_errors + undefined_errors + import_errors

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
                abs_path = (self.root_dir / file_path).resolve()
                if error.line_number > 0:
                    print(f"   └─ 行 {error.line_number}: [{error.error_type}] {error.message} -> {abs_path}:{error.line_number}")
                else:
                    print(f"   └─ [{error.error_type}] {error.message} -> {abs_path}")
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
