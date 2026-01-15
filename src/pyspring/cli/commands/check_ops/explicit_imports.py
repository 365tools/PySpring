"""
显式导入检查器

将 `from package import Symbol` 转换为 `from package.module import Symbol`
当 Symbol 未在 package/__init__.py 中显式定义，但存在于 package/module.py 中时。
这种转换有助于解决 IDE（如 PyCharm/VSCode）在处理动态导入或不完整的 __init__ 文件时无法识别符号的问题。
"""
import ast
import os
from typing import List, Optional

from pyspring.cli.component.files.ignore import get_ignore_list
from pyspring.cli.core.ui import print_section, print_success, print_warning, print_info


def import_range(start, end):
    """格式化行号范围"""
    if start == end: return str(start)
    return f"{start}-{end}"


class SymbolDefinitionVisitor(ast.NodeVisitor):
    def __init__(self, target_symbol: str):
        self.target_symbol = target_symbol
        self.found = False

    def visit_ClassDef(self, node: ast.ClassDef):
        if node.name == self.target_symbol:
            self.found = True

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name == self.target_symbol:
            self.found = True

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if node.name == self.target_symbol:
            self.found = True

    # 也可以检查赋值语句，但这对于变量来说可能有风险。


def find_symbol_in_package(package_dir: str, symbol: str) -> List[str]:
    """
    在包的 .py 文件中搜索符号（不包括 __init__.py）。
    如果找到，返回找到该符号的所有子模块名称列表。
    """
    found_modules = []
    if not os.path.exists(package_dir):
        return []

    for root, _, files in os.walk(package_dir):
        # 目前只扫描顶级子文件
        if root != package_dir:
            continue

        for file in files:
            if file == '__init__.py' or not file.endswith('.py'):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 先进行快速字符串检查
                if symbol not in content:
                    continue

                tree = ast.parse(content)
                visitor = SymbolDefinitionVisitor(symbol)
                visitor.visit(tree)

                if visitor.found:
                    found_modules.append(file[:-3])
            except Exception:
                continue

    return found_modules


class ImportExpander(ast.NodeVisitor):
    def __init__(self, file_path: str, root_path: str):
        self.file_path = file_path
        self.root_path = root_path
        self.replacements = []  # 列表元素: (lineno, original_line, new_line)
        self.warnings = []  # 收集歧义警告信息

    def resolve_package_path(self, module_name: str, level: int) -> Optional[str]:
        """将模块名 + 层级解析为目录路径"""
        # 计算当前目录
        current_dir = os.path.dirname(self.file_path)

        target_dir = current_dir

        # 处理相对导入
        if level > 0:
            for _ in range(level - 1):  # . -> 当前, .. -> 父级
                target_dir = os.path.dirname(target_dir)

        # 现在追加模块部分
        if module_name:
            parts = module_name.split('.')
            target_dir = os.path.join(target_dir, *parts)

        return target_dir

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # 检查是否从包中导入
        # node.module: 'security_ops'
        # node.level: 1 (表示 .), 0 表示绝对导入

        # 我们针对可能是包的导入。
        target_path = self.resolve_package_path(node.module, node.level)

        # 检查 target_path 是否指向目录
        # 它可能是文件 (security_ops.py) 或目录 (security_ops/)
        if not target_path or not os.path.isdir(target_path):
            # 尝试检查如果是绝对导入，是否存在于项目根目录相对路径
            if node.level == 0 and node.module:
                # 启发式：尝试从根目录解析
                abs_path = os.path.join(self.root_path, *node.module.split('.'))
                if os.path.isdir(abs_path):
                    target_path = abs_path
                else:
                    pass

        if target_path and os.path.isdir(target_path) and os.path.exists(os.path.join(target_path, '__init__.py')):
            # 这是一个包。

            names_to_rewrite = []  # (name, alias, sub_mod)

            for alias in node.names:
                if alias.name == '*': continue

                found_modules = find_symbol_in_package(target_path, alias.name)

                if not found_modules:
                    continue

                if len(found_modules) > 1:
                    # 发现歧义，记录警告并跳过（保持原样）
                    self.warnings.append(f"符号 '{alias.name}' 在多个子模块中定义: {found_modules}。跳过处理。")
                    continue

                # 只有唯一匹配才进行重写
                sub_mod = found_modules[0]
                names_to_rewrite.append((alias.name, alias.asname, sub_mod))

            if names_to_rewrite:
                # 我们有需要扩展的候选者。
                # 按子模块分组
                import_groups = {}  # sub_mod -> [ (name, asname) ]

                original_names = [(a.name, a.asname) for a in node.names]
                keep_names = []

                for name, asname in original_names:
                    # 检查此名称是否在我们的重写列表中
                    found = False
                    for r_name, r_as, r_mod in names_to_rewrite:
                        if r_name == name:
                            if r_mod not in import_groups: import_groups[r_mod] = []
                            import_groups[r_mod].append((name, asname))
                            found = True
                            break
                    if not found:
                        keep_names.append((name, asname))

                new_lines = []

                # 基础模块字符串
                base_mod = ""
                if node.level > 0:
                    base_mod += "." * node.level
                if node.module:
                    base_mod += node.module

                if keep_names:
                    kept_str = ", ".join([f"{n} as {a}" if a else n for n, a in keep_names])
                    new_lines.append(f"from {base_mod} import {kept_str}")

                for sub_mod, imports in import_groups.items():
                    imp_str = ", ".join([f"{n} as {a}" if a else n for n, a in imports])
                    # 构建新的模块路径
                    # 例如 .package.sub
                    new_lines.append(f"from {base_mod}.{sub_mod} import {imp_str}")

                self.replacements.append({
                    'lineno': node.lineno,
                    'end_lineno': getattr(node, 'end_lineno', node.lineno),
                    'new_lines': new_lines
                })


def check_and_fix_imports(root_path: str, scan_path: str, fix: bool = False):
    print_section("检查并扩展导入路径")

    ignore_list = get_ignore_list(root_path)
    count = 0
    files_fixed = 0

    abs_scan_path = os.path.abspath(scan_path)

    for root, dirs, files in os.walk(abs_scan_path):
        dirs[:] = [d for d in dirs if d not in ignore_list]

        for file in files:
            if not file.endswith('.py'): continue

            file_path = os.path.join(root, file)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue

                expander = ImportExpander(file_path, root_path)
                expander.visit(tree)

                if expander.replacements or expander.warnings:
                    if expander.replacements:
                        count += len(expander.replacements)

                    print_info(f"文件: {os.path.relpath(file_path, root_path)}")

                    # 首先打印警告
                    for w in expander.warnings:
                        print_warning(f"  ⚠ {w}")

                    # 倒序排序替换，以保持行号有效
                    expander.replacements.sort(key=lambda x: x['lineno'], reverse=True)

                    lines = content.splitlines()

                    for rep in expander.replacements:
                        start = rep['lineno'] - 1
                        end = rep['end_lineno']

                        orig_text = "\n".join(lines[start:end])
                        new_text = "\n".join(rep['new_lines'])

                        print_warning(f"  行 {import_range(start + 1, end)}: {orig_text.strip()} -> {new_text.replace(chr(10), ' | ')}")

                        if fix:
                            # 替换行
                            # 注意：简单的替换，如果不小心可能会搞乱多行导入的格式
                            # 但我们生成的是干净的新行。
                            lines[start:end] = rep['new_lines']

                    if fix and expander.replacements:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("\n".join(lines) + "\n")  # 规范化换行符
                        files_fixed += 1

            except Exception as e:
                # logger.debug(e)
                pass

    if count == 0:
        print_success("未发现模糊导入。")
    else:
        print_section("摘要")
        print(f"发现可扩展的导入: {count}")
        if fix:
            print(f"已修复文件数: {files_fixed}")
        else:
            print_info("请运行 --fix 以应用更改。")


def run_check_explicit_imports(args):
    """入口点"""
    check_and_fix_imports(os.getcwd(), args.path, fix=args.fix)
