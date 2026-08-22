"""
CLI 集成测试：init 命令生成项目。

验证普通 init 和 init --example 都能生成完整项目结构。
"""

import os


def test_init_creates_project(cli, project_dir):
    """普通 init 应生成标准项目结构。"""
    rc, out = cli(["init", str(project_dir)], cwd=".")
    assert rc == 0, f"init failed: {out[:300]}"

    expected = [
        "pyproject.toml",
        "README.md",
        "main.py",
        ".env",
        "app",
        "config",
        "scripts",
        "tests",
    ]
    for name in expected:
        assert os.path.exists(os.path.join(project_dir, name)), f"missing {name}"


def test_init_creates_main_and_config(cli, project_dir):
    """init 应生成可运行的 main.py 和配置文件。"""
    rc, out = cli(["init", str(project_dir)], cwd=".")
    assert rc == 0, f"init failed: {out[:300]}"

    main_py = os.path.join(project_dir, "main.py")
    assert os.path.exists(main_py)
    content = open(main_py, encoding="utf-8").read()
    # 命名空间包 API（重构后）
    assert "pyspring.core.ioc" in content or "pyspring.core" in content


def test_init_example_creates_demo(cli, project_dir):
    """init --example 应生成包含业务模块的完整示例。"""
    rc, out = cli(["init", str(project_dir), "--example"], cwd=".")
    assert rc == 0, f"init --example failed: {out[:300]}"

    app_dir = os.path.join(project_dir, "app")
    assert os.path.isdir(app_dir), "missing app/ dir"
    for sub in ["api", "services", "repositories", "models", "config", "extensions"]:
        assert os.path.isdir(os.path.join(app_dir, sub)), f"missing app/{sub}"


def test_init_pyproject_requires_python_314(cli, project_dir):
    """生成的 pyproject 应要求 Python 3.14+。"""
    rc, out = cli(["init", str(project_dir)], cwd=".")
    assert rc == 0, f"init failed: {out[:300]}"
    content = open(os.path.join(project_dir, "pyproject.toml"), encoding="utf-8").read()
    assert 'requires-python = ">=3.14"' in content


def test_init_creates_readme(cli, project_dir):
    """init 应生成 README.md（pyproject 引用它）。"""
    rc, out = cli(["init", str(project_dir)], cwd=".")
    assert rc == 0, f"init failed: {out[:300]}"
    readme = os.path.join(project_dir, "README.md")
    assert os.path.exists(readme), "missing README.md"
    assert open(readme, encoding="utf-8").read().strip() != ""
