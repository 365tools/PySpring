"""
BasedPyright Type-Check Checker

调用 basedpyright 对项目做深度类型检查（type checking），
能精确复现 IDE（VSCode/PyCharm）中基于 pyright 语言服务器的诊断，
如 reportDeprecated / reportExplicitAny / reportAbstractUsage / reportUnknownMemberType 等。

与 references（纯 AST 静态分析）互补：
- references：检测未定义名称、缺失导入（AST 层面）
- basedpyright：检测类型推断问题（泛型、Any、弃用类型、抽象类实例化等）
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from typing import Any, List, Dict, Optional

from pyspring.cli.core.ui.console import (
    print_title, print_info, print_error, print_warning,
    print_issue, print_section, print_success,
)


class BasedPyrightChecker:
    """
    基于 basedpyright 的类型检查器。

    覆盖 BaseChecker.run() 做整体扫描（basedpyright 是项目级类型推断，
    不适合逐文件独立扫描）。
    """

    def __init__(self, target_path: str = '.', severity: str = 'error',
                 rules: Optional[List[str]] = None):
        """
        :param target_path: 要扫描的项目根路径（源码目录）
        :param severity: 输出级别: 'error' (默认) | 'warning' | 'all'
        :param rules: 仅显示指定规则（可选，如 ['reportDeprecated', 'reportExplicitAny']）
        """
        self.target_path = os.path.abspath(target_path)
        self.severity = severity
        self.rules = set(rules or [])

        # 统计
        self.total_issues = 0
        self.files_with_issues = 0
        self.summary = {}

    @property
    def title(self) -> str:
        return "BasedPyright Type Check"

    # ---- 定位可执行文件 ----

    @staticmethod
    def _find_executable() -> Optional[list[str]]:
        """按优先级查找 basedpyright 可执行命令列表。"""
        # 1. 当前 Python 环境的模块（作为依赖安装）
        # 用 find_spec 检查，避免顶层 import 触发静态导入检测误报
        if importlib.util.find_spec("basedpyright") is not None:
            return [sys.executable, "-m", "basedpyright"]
        # 2. 系统 PATH 中的命令
        for cmd in ("basedpyright", "basedpyright.cmd"):
            found = shutil.which(cmd)
            if found:
                return [found]
        # 3. npx（临时拉取，无需全局安装）
        npx = shutil.which("npx") or shutil.which("npx.cmd")
        if npx:
            return [npx, "--yes", "basedpyright"]
        return None

    # ---- 主流程 ----

    def run(self) -> bool:
        print_title(f"{self.title}: {self.target_path}")

        exe = self._find_executable()
        if exe is None:
            print_error(
                "basedpyright 未找到。请安装：\n"
                "  pip install basedpyright     # 或\n"
                "  uv add --dev basedpyright"
            )
            return False

        cmd = exe + ["--outputjson", self.target_path]
        print_info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as e:
            print_error(f"无法执行 basedpyright: {e}")
            return False

        try:
            data = self._parse_output(result.stdout)
        except (json.JSONDecodeError, ValueError) as e:
            print_error(f"解析 basedpyright 输出失败: {e}")
            if result.stderr:
                print_warning(result.stderr[-500:])
            return False

        self._process_diagnostics(data)
        self._print_report()

        return self.total_issues == 0

    def _parse_output(self, raw: str) -> dict[str, Any]:
        """从 basedpyright 原始输出中提取 JSON。"""
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start < 0 or end <= 0:
            raise ValueError("basedpyright 输出中未找到 JSON")
        return json.loads(raw[start:end])

    def _process_diagnostics(self, data: dict[str, Any]):
        """过滤并统计诊断。"""
        self.summary = data.get("summary", {})
        diags = data.get("generalDiagnostics", [])

        file_issues: dict[str, list[dict[str, Any]]] = {}
        for d in diags:
            severity = d.get("severity", "information")
            rule = d.get("rule", "")
            # 按严重度过滤
            if not self._passes_severity(severity):
                continue
            # 按规则过滤
            if self.rules and rule not in self.rules:
                continue

            path = d.get("file", "")
            line0 = (d.get("range", {}).get("start", {}) or {}).get("line", 0)
            file_issues.setdefault(path, []).append({
                "line": line0 + 1,          # 转 1-based
                "message": d.get("message", ""),
                "severity": severity,
                "rule": rule,
            })

        for path in sorted(file_issues):
            issues = file_issues[path]
            self.files_with_issues += 1
            for issue in issues:
                self.total_issues += 1
                self._print_issue(path, issue)

    def _passes_severity(self, severity: str) -> bool:
        if self.severity == "all":
            return True
        if self.severity == "warning":
            return severity in ("error", "warning")
        # default: error only
        return severity == "error"

    def _print_issue(self, path: str, issue: dict[str, Any]):
        level = "warning" if issue["severity"] == "warning" else "error"
        rule = f"[{issue['rule']}] " if issue["rule"] else ""
        print_issue(
            str(issue["line"]),
            f"{rule}{issue['message']}",
            file_path=path,
            level=level,
        )

    def _print_report(self):
        print_section("Summary")
        analyzed = self.summary.get("filesAnalyzed", 0)
        print_info(f"Files analyzed: {analyzed}")

        if self.total_issues == 0:
            print_success("No issues found.")
        else:
            print(f"Found {self.total_issues} issue(s) in {self.files_with_issues} file(s).")

        # 提示如何调整
        if self.total_issues > 0:
            print_info(
                "Tip: use --severity warning|all 查看 warning 级问题，"
                "--rules <rule> 过滤特定规则"
            )


def run_check_basedpyright(args):
    """Check 子命令入口。"""
    target = getattr(args, 'target', None) or getattr(args, 'path', None) or '.'
    severity = getattr(args, 'severity', 'error')
    rules_raw = getattr(args, 'rules', '') or ''
    rules = [r.strip() for r in rules_raw.split(',') if r.strip()]

    checker = BasedPyrightChecker(target_path=target, severity=severity, rules=rules)
    return checker.run()
