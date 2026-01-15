"""
Explicit Import Checker

Converts `from package import Symbol` to `from package.module import Symbol`
when the Symbol is not explicitly defined in package/__init__.py but exists in package/module.py.
This conversion helps resolve issues where IDEs (like PyCharm/VSCode) fail to recognize symbols
when dealing with dynamic imports or incomplete __init__ files.
"""
import ast
import os
from typing import List, Optional

from pyspring.cli.component.files.ignore import get_ignore_list
from pyspring.cli.core.ui import (
    print_title, print_file_header, print_issue, print_summary
)


def import_range(start, end):
    """Format line number range"""
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


def find_symbol_in_package(package_dir: str, symbol: str) -> List[str]:
    """
    Search for a symbol in .py files within the package (excluding __init__.py).
    If found, returns a list of all sub-module names where the symbol is found.
    """
    found_modules = []
    if not os.path.exists(package_dir):
        return []

    for root, _, files in os.walk(package_dir):
        # Currently only scans top-level child files
        if root != package_dir: 
            continue

        for file in files:
            if file == '__init__.py' or not file.endswith('.py'):
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Perform quick string check first
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
        """Resolve module name + level to directory path"""
        # Calculate current directory
        current_dir = os.path.dirname(self.file_path)

        target_dir = current_dir

        # Handle relative imports
        if level > 0:
            for _ in range(level - 1):  # . -> current, .. -> parent
                target_dir = os.path.dirname(target_dir)

        # Now append module part
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
    print_title("Checking and Expanding Imports")
    
    ignore_list = get_ignore_list(root_path)
    total_issues = 0  # Logical count of replacements
    files_with_issues = 0
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

                has_issues = False

                # Handling Warnings
                if expander.warnings:
                    has_issues = True
                    print_file_header(file_path)
                    for w in expander.warnings:
                        print_issue("0", w, file_path, level='warning')

                # Handling Replacements
                if expander.replacements:
                    has_issues = True
                    if not expander.warnings:  # Print header if not already printed
                        print_file_header(file_path)

                    total_issues += len(expander.replacements)
                    
                    # 倒序排序替换，以保持行号有效
                    expander.replacements.sort(key=lambda x: x['lineno'], reverse=True)

                    lines = content.splitlines()

                    for rep in expander.replacements:
                        start = rep['lineno'] - 1
                        end = rep['end_lineno']

                        orig_text = "\n".join(lines[start:end])
                        new_text = "\n".join(rep['new_lines'])

                        rng = import_range(start + 1, end)
                        msg = f"{orig_text.strip()} -> {new_text.replace(chr(10), ' | ')}"
                        print_issue(rng, msg, file_path, level='warning')
                        
                        if fix:
                            # 替换行
                            lines[start:end] = rep['new_lines']

                    if fix:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("\n".join(lines) + "\n")  # 规范化换行符
                        files_fixed += 1

                if has_issues:
                    files_with_issues += 1
                        
            except Exception as e:
                pass

    print_summary(total_issues, files_with_issues, files_fixed, fixable=not fix)


def run_check_explicit_imports(args):
    """入口点"""
    check_and_fix_imports(os.getcwd(), args.path, fix=args.fix)
