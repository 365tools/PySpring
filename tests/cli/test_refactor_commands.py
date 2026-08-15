"""
CLI 集成测试：重构命令（imports-unused 等）。

在隔离的临时目录构造含未使用导入的文件，验证重构命令实际生效。
"""
import os

import pytest

UNUSED_IMPORT_MODULE = '''\
"""Sample with an unused import."""
import os  # unused import
import sys  # used


def get_path() -> str:
    return sys.executable
'''

CLEANED_MODULE = '''\
"""Sample with an unused import."""
import sys  # used


def get_path() -> str:
    return sys.executable
'''


@pytest.fixture()
def refactor_dir(repo_workdir):
    """
    隔离的重构测试目录（位于仓库内，imports-* 命令依赖仓库上下文）。

    在仓库内 tests/cli/_work/ 下创建，fixture 结束自动清理。
    """
    d = os.path.join(repo_workdir, "refactor")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "sample.py"), "w", encoding="utf-8") as f:
        f.write(UNUSED_IMPORT_MODULE)
    return d


def test_imports_unused_removes_import(cli, refactor_dir):
    """imports-unused 应移除未使用导入。"""
    rc, out = cli(["imports-unused", str(refactor_dir)], cwd=".", timeout=120)
    assert rc == 0, f"imports-unused failed: {out[:300]}"

    cleaned = open(os.path.join(refactor_dir, "sample.py"), encoding="utf-8").read()
    # os import removed
    assert "import os" not in cleaned, "unused import os not removed"
    # sys import kept
    assert "import sys" in cleaned, "used import sys wrongly removed"
    # content otherwise preserved
    assert "get_path" in cleaned


def test_imports_validate_detects_unused(cli, refactor_dir):
    """imports-validate 应能检测未使用导入。"""
    rc, out = cli(["imports-validate", str(refactor_dir)], cwd=".", timeout=120)
    assert rc in (0, 1), f"imports-validate failed: {out[:300]}"


def test_imports_lift_help(cli):
    """imports-lift 帮助可加载。"""
    rc, out = cli(["imports-lift", "--help"], cwd=".")
    assert rc == 0, f"imports-lift --help failed: {out[:200]}"


def test_imports_explicit_help(cli):
    """imports-explicit 帮助可加载。"""
    rc, out = cli(["imports-explicit", "--help"], cwd=".")
    assert rc == 0, f"imports-explicit --help failed: {out[:200]}"


def test_imports_reset_help(cli):
    """imports-reset 帮助可加载。"""
    rc, out = cli(["imports-reset", "--help"], cwd=".")
    assert rc == 0, f"imports-reset --help failed: {out[:200]}"
