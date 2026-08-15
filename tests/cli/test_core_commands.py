"""
CLI 集成测试：核心用户命令（check / clean / status / security / cache / diagnose）。

这些命令在隔离的临时项目中执行，验证基本功能。
"""
import os

import pytest


@pytest.fixture()
def created_project(cli, project_dir):
    """在隔离目录生成一个 init 项目供命令测试。"""
    rc, out = cli(["init", str(project_dir)], cwd=".")
    assert rc == 0, f"init failed: {out[:300]}"
    return project_dir


def test_status(cli, created_project):
    """status 应报告环境状态。"""
    rc, out = cli(["status"], cwd=created_project)
    assert rc == 0, f"status failed: {out[:300]}"
    assert "pyspring" in out.lower() or "version" in out.lower()


def test_check(cli, created_project):
    """check 应运行项目检查。"""
    rc, out = cli(["check"], cwd=created_project)
    assert rc == 0, f"check failed: {out[:300]}"


def test_security_gen_key(cli, created_project):
    """security gen-key 应生成密钥。"""
    rc, out = cli(["security", "gen-key"], cwd=created_project)
    assert rc == 0, f"security gen-key failed: {out[:300]}"
    assert len(out) > 10, "gen-key produced no output"


def test_cache_clear(cli, created_project):
    """cache 应成功清除缓存。"""
    rc, out = cli(["cache"], cwd=created_project)
    assert rc == 0, f"cache failed: {out[:300]}"


def test_clean(cli, created_project):
    """clean 应清理临时文件（在隔离项目内，无害）。"""
    rc, out = cli(["clean"], cwd=created_project)
    assert rc == 0, f"clean failed: {out[:300]}"


def test_diagnose(cli, created_project):
    """diagnose 应运行诊断。"""
    rc, out = cli(["diagnose"], cwd=created_project)
    assert rc == 0, f"diagnose failed: {out[:300]}"


def test_config_verify(cli, created_project):
    """config-verify 应验证配置。"""
    rc, out = cli(["config-verify"], cwd=created_project)
    assert rc == 0, f"config-verify failed: {out[:300]}"


def test_encoding(cli):
    """encoding 应扫描仓库文件编码。"""
    rc, out = cli(["encoding", "packages"], cwd=".")
    assert rc == 0, f"encoding failed: {out[:300]}"


def test_meta_check(cli):
    """meta check 应检查元数据。"""
    rc, out = cli(["meta", "check"], cwd=".")
    assert rc == 0, f"meta check failed: {out[:300]}"
