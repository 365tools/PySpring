"""
CLI 集成测试：分析/诊断命令（imports-* / references / basedpyright）。

这些命令对 packages/ 源码做只读分析（imports-unused 除外，单独测试）。
"""

import pytest


def test_imports_validate(cli):
    """imports-validate 应能扫描并报告导入问题（无硬失败）。"""
    rc, out = cli(["imports-validate", "packages"], cwd=".", timeout=120)
    assert rc in (0, 1), f"imports-validate failed: {out[:300]}"


def test_imports_circular(cli):
    """imports-circular 应扫描循环依赖。"""
    rc, out = cli(["imports-circular", "packages"], cwd=".", timeout=120)
    assert rc in (0, 1), f"imports-circular failed: {out[:300]}"


def test_references(cli):
    """references 应扫描引用（只读）。"""
    rc, out = cli(["references", "packages"], cwd=".", timeout=180)
    assert rc in (0, 1), f"references failed: {out[:300]}"


@pytest.mark.slow
def test_basedpyright(cli):
    """basedpyright 应对核心包做类型检查（慢命令）。"""
    rc, out = cli(
        ["basedpyright", "packages/pyspring-core/src/pyspring/core/ioc"],
        cwd=".",
        timeout=300,
    )
    assert rc in (0, 1, 2), f"basedpyright failed: {out[:300]}"
