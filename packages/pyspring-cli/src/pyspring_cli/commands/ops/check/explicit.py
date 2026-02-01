"""
Explicit Import Checker

Converts `from package import Symbol` to `from package.module import Symbol`
when the Symbol is not explicitly defined in package/__init__.py but exists in package/module.py.
This conversion helps resolve issues where IDEs (like PyCharm/VSCode) fail to recognize symbols
when dealing with dynamic imports or incomplete __init__ files.
"""
import ast
import os
from typing import Optional

from pyspring_cli.core.utils.code import get_indentation, apply_indentation
from .base import BaseChecker
from .imports.static import find_symbol_in_package
from ....core.utils.filesystem import get_ignore_list


def import_range(start, end):
    """Format line number range"""
    if start == end: return str(start)
    return f"{start}-{end}"


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
        # node.module: 'security'
        # node.level: 1 (表示 .), 0 表示绝对导入

        # 我们针对可能是包的导入。
        target_path = self.resolve_package_path(node.module or "", node.level)

        # 检查 target_path 是否指向目录
        # 它可能是文件 (security.py) 或目录 (security/)
        if not target_path or not os.path.isdir(target_path):
            # 尝试检查如果是绝对导入，是否存在于项目根目录相对路径
            if node.level == 0 and node.module:
                # 启发式：尝试从根目录解析
                abs_path = os.path.join(self.root_path, *node.module.split('.'))
                if os.path.isdir(abs_path):
                    target_path = abs_path
                else:
                    # 尝试 src 目录 (针对 src-layout 项目)
                    src_abs_path = os.path.join(self.root_path, 'src', *node.module.split('.'))
                    if os.path.isdir(src_abs_path):
                        target_path = src_abs_path

        if target_path and os.path.isdir(target_path) and os.path.exists(os.path.join(target_path, '__init__.py')):
            # Check if target_path is ignored
            ignored_set = get_ignore_list(self.root_path)
            # Normalize path for checking
            norm_target = os.path.normpath(target_path)
            parts = norm_target.split(os.sep)

            # If any part of the path is in ignored set (like .venv), skip it
            # We also check for hidden directories starting with '.' which are implicitly ignored
            should_ignore = False
            for part in parts:
                if part in ignored_set or (part.startswith('.') and part != '.' and part != '..'):
                    # Only ignore if it is not current/parent dir marker
                    should_ignore = True
                    break

            if should_ignore:
                return

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


class ExplicitImportChecker(BaseChecker):
    @property
    def title(self):
        return "Explicit Import Expansion"

    def __init__(self, target_path):
        super().__init__(target_path, ['.py'])
        self.root_path = os.getcwd()

    def check_file(self, file_path: str, fix: bool = False, **kwargs) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return False

        expander = ImportExpander(file_path, self.root_path)
        expander.visit(tree)

        has_issues = False

        if expander.warnings and fix:
            for w in expander.warnings:
                self.add_issue(file_path, 0, f"{w} -> Manual resolution required", level='error')

        if expander.replacements:
            has_issues = True
            expander.replacements.sort(key=lambda x: x['lineno'], reverse=True)
            lines = content.splitlines()

            file_modifications = False

            for rep in expander.replacements:
                start = rep['lineno'] - 1
                end = rep['end_lineno']

                # Handling safe slice
                if start < 0: start = 0
                if end > len(lines): end = len(lines)

                # Capture original indentation from the first line of the block
                indentation = get_indentation(lines[start])
                
                orig_text = " | ".join(lines[start:end])
                new_text = " | ".join(rep['new_lines'])

                msg = f"Implicit import -> Explicit: {orig_text.strip()} => {new_text}"

                if fix:
                    # Apply indentation to new lines
                    fixed_new_lines = apply_indentation(rep['new_lines'], indentation)
                    lines[start:end] = fixed_new_lines
                    file_modifications = True
                    self.record_fix(file_path, rep['lineno'], f"{msg} -> Fixed")
                else:
                    self.add_issue(file_path, rep['lineno'], msg, level='warning')

            if fix and file_modifications:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                except Exception as e:
                    self.add_issue(file_path, 0, f"Error saving file: {e}", level='error')

        else:
            # If no replacements found but issues might exist (e.g. only warnings or not found)
            if not expander.warnings and not expander.replacements:
                # Check for potentials that failed
                pass  # Currently visitor doesn't track "failed candidates" explicitly except via warnings

        return has_issues


def run_check_explicit_imports(args):
    target_path = getattr(args, 'path', '.')
    checker = ExplicitImportChecker(target_path)
    return checker.run(fix=args.fix)
