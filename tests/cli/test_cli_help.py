"""
CLI 集成测试：验证所有命令可加载并显示帮助。

确保每个命令都正确注册且能解析参数（返回码 0 + 包含 usage）。
"""
import pytest

ALL_COMMANDS = [
    "uv", "init", "check", "clean", "security",
    "dev", "meta",
    "basedpyright", "cache", "config-verify", "diagnose", "encoding",
    "gen-key", "imports-circular", "imports-explicit", "imports-lift",
    "imports-refactor", "imports-reset", "imports-unused", "imports-validate",
    "init-sync", "install", "rebuild", "references", "setup", "status",
    "templates-sync",
]


@pytest.mark.parametrize("command", ALL_COMMANDS)
def test_command_loads_help(cli, command):
    """每个命令都应能加载并显示 usage 帮助。"""
    rc, out = cli([command, "--help"], cwd=".")
    assert rc == 0, f"{command} --help failed (exit {rc}): {out[:200]}"
    assert "usage:" in out.lower(), f"{command} --help missing usage: {out[:200]}"


def test_version_flag(cli):
    """-v 应显示版本号。"""
    rc, out = cli(["-v"], cwd=".")
    assert rc == 0, f"-v failed: {out[:200]}"
    assert "pyspring" in out.lower(), f"-v missing version: {out[:200]}"


def test_no_args_shows_banner(cli):
    """无参数应显示 banner 并提示用法（返回码 0 或 1 均可）。"""
    rc, out = cli([], cwd=".")
    assert rc in (0, 1), f"no-args failed (exit {rc}): {out[:200]}"
    assert out.strip() != "", "no-args produced no output"
