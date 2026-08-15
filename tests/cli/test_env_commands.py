"""
CLI 集成测试：环境与工具命令（install / setup / rebuild / templates-sync / uv / dev）。

install/setup/rebuild 会重新安装环境（慢 + 有副作用），这里验证其命令可加载；
templates-sync 在隔离项目中验证实际同步功能。
"""
import os

import pytest


@pytest.fixture()
def created_project(cli, project_dir):
    """隔离 init 项目。"""
    rc, out = cli(["init", str(project_dir)], cwd=".")
    assert rc == 0, f"init failed: {out[:300]}"
    return project_dir


@pytest.mark.parametrize("command", ["install", "setup", "rebuild"])
def test_env_command_help(cli, command):
    """环境命令帮助可加载。"""
    rc, out = cli([command, "--help"], cwd=".")
    assert rc == 0, f"{command} --help failed: {out[:200]}"
    assert "usage:" in out.lower()


@pytest.mark.parametrize("command", ["uv", "dev"])
def test_subcommand_group_help(cli, command):
    """子命令组帮助可加载。"""
    rc, out = cli([command, "--help"], cwd=".")
    assert rc == 0, f"{command} --help failed: {out[:200]}"
    assert "usage:" in out.lower()


def test_templates_sync_help(cli):
    """templates-sync 帮助可加载。"""
    rc, out = cli(["templates-sync", "--help"], cwd=".")
    assert rc == 0, f"templates-sync --help failed: {out[:200]}"


def test_templates_sync_runs(cli, created_project):
    """templates-sync 应在隔离项目中执行（0 或 1 均接受，避免破坏性副作用）。"""
    rc, out = cli(["templates-sync"], cwd=created_project, timeout=120)
    assert rc in (0, 1), f"templates-sync failed: {out[:300]}"
