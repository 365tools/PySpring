"""
PySpring CLI 集成测试配置

使用隔离的 PYSPRING_HOME 和临时项目目录，避免污染真实工作区。
所有命令通过 subprocess 调用真实 CLI（python -m pyspring.cli.main），
验证 CLI 的实际行为（返回码 + 输出）。
"""
import os
import subprocess
import sys

import pytest


@pytest.fixture()
def cli_env(tmp_path):
    """隔离的 CLI 运行环境：设置 PYSPRING_HOME 指向临时目录。"""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["PYSPRING_HOME"] = str(home)
    # 确保 tests/packages 源码路径可被 CLI 的依赖找到
    env["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    return env


def _run_cli(args, cwd, env, timeout=120):
    """调用真实 CLI，返回 (returncode, stdout+stderr)。"""
    cmd = [sys.executable, "-m", "pyspring.cli.main"] + list(args)
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            cwd=str(cwd), env=env, timeout=timeout,
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""
    except Exception as exc:
        return "ERROR", str(exc)


@pytest.fixture()
def cli(cli_env):
    """CLI 调用辅助：cli.run(args, cwd, timeout) -> (returncode, output)。"""

    def _run(args, cwd, timeout=120):
        return _run_cli(args, cwd, cli_env, timeout)

    return _run


@pytest.fixture()
def project_dir(tmp_path):
    """临时项目目录（隔离，避免污染工作区）。"""
    return tmp_path / "project"


@pytest.fixture()
def repo_workdir(tmp_path):
    """
    仓库内的隔离工作目录。

    部分命令（如 imports-*）依赖仓库/git 上下文，在系统 temp（仓库外）
    的路径下会失败。此 fixture 在仓库内创建隔离目录，测试后自动清理。
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    work = os.path.join(repo_root, "tests", "cli", "_work")
    os.makedirs(work, exist_ok=True)
    yield work
    # 清理（仅删除本 fixture 创建的内容）
    import shutil
    if os.path.isdir(work):
        shutil.rmtree(work, ignore_errors=True)
