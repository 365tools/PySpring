# 更新日志

PySpring 的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

> 此处累积**尚未正式发版**的变更（多次迭代的更新统一聚合在这里）。
> 正式发版时：把本小节重命名为 `[版本号] - 日期`，并在顶部新建一个空的 `## [Unreleased]`。

### 新增
- （待补充）

### 变更
- （待补充）

### 修复
- （待补充）

---

## [0.0.1] - 2026-08-15

### 🎯 全新实现：Spring Boot for Python

**PySpring 全新实现**，采用 Spring Boot 风格的 **Starter 化 + PEP 420 命名空间包** 架构，生产环境就绪。

### 架构

- ✅ **PEP 420 命名空间包**：所有 Starter 共享统一 `pyspring` 顶层命名空间，发行包名与导入名解耦。
  - `pyspring-core` → `pyspring.core`（IoC / AOP / 日志 / 配置，**始终加载**）
  - `pyspring-security` → `pyspring.security`（认证 JWT、授权 RBAC、密码编码）
  - `pyspring-repositories` → `pyspring.repositories`（数据库 ORM、缓存抽象）
  - `pyspring-web` → `pyspring.web`（统一响应、全局异常）
  - `pyspring-health` → `pyspring.health`（健康检查）
  - `pyspring-cli` → `pyspring.cli`（命令行工具）
  - `pyspring`（聚合包）→ `pyspring`（含项目模板）
- ✅ **Starter 自动配置**：通过 Python `entry-points`（`pyspring.starters` 组）声明式发现与装配，即插即用，不引用不影响核心。
- ✅ **uv workspace 管理**：根 `pyproject.toml` 统一管理 7 个子包。

### 核心能力

- **智能 IoC 容器**：自动组件扫描、依赖注入、循环依赖 DAG 检测、启动缓存。
- **AOP 切面编程**：`@Before` / `@After` / `@Around` 运行时动态代理。
- **三层配置系统**：框架默认值 → 用户配置 → 环境变量，深度合并与覆盖。
- **生产级安全**：JWT 认证、RBAC 授权、BCrypt 密码编码、Token 负载加密。
- **统一数据抽象**：PostgreSQL / MySQL / SQLite 透明切换，Redis / Memory / Memcached 缓存。
- **应用生命周期**：Startup Initializers / Shutdown Handlers 钩子体系。
- **统一响应**：`Response.success()` / `Response.error()`，全局异常处理。

### 工程与质量

- ✅ **零容忍质量门禁**：`pyspring check --all` 必须 0 error / 0 warning。
- ✅ **完整类型注解**：`pyright` 全项目 0 error。
- ✅ **测试按 Starter 拆分**：`tests/{core,health,repositories,security,web}/` + `tests/cli/`，**110 个测试用例**（51 单元 + 59 CLI 集成）全部通过，pytest-xdist 并行下 22 秒完成。
- ✅ **CLI 集成测试**：`tests/cli/` 通过 subprocess 端到端验证全部 27 个命令。
- ✅ **CLI 工具**：`pyspring init` / `check` / `dev` / `clean` / `security` / `uv`。

### 本阶段修复与优化

- **CLI 模板对齐 PEP 420**：修复命名空间导入（`pyspring.core.ioc` / `pyspring.core.log`）、动态 `__all__` 导入、RBAC 表不一致、`container.yaml` 契约、`pyproject.toml` 规范（Python 3.14 / setuptools / ruff）。
- **依赖升级**：`requires-python` 提升到 `>=3.14`；依赖下限升级到最新稳定版（fastapi 0.141 / redis 8 / cryptography 50 / uvicorn 0.52 / pydantic 2.13 等）；移除废弃依赖（`dependency-injector`、`fastapi-users`、`black`/`flake8`/`mypy`）。
- **CI/CD 适配多包**：GitHub workflows 改为 uv workspace 多包构建/发布，TestPyPI 全自动 + 生产 PyPI 手动批准保护。
- **清理与整合**：删除过时 `examples/`、`setup.py`、`MANIFEST.in`、一次性脚本；整合发布脚本支持全部 7 个包。
- **测试性能**：引入 pytest-xdist 并行执行（完整套件 22s，较串行提速 3x+），相关实践文档见 `docs/00-architecture/03-TESTING.md`。

---

## 贡献

我们欢迎贡献！

- **Bug 报告**: [GitHub Issues](https://github.com/eavelabs-community/py-spring/issues)
- **功能请求**: [GitHub Discussions](https://github.com/eavelabs-community/py-spring/discussions)
- **Pull Requests**: [GitHub Pull Requests](https://github.com/eavelabs-community/py-spring/pulls)

---

## 许可证

本项目采用 Apache License 2.0 许可 - 详见 [LICENSE](LICENSE) 文件。

---

## 链接

- **文档**: [docs/](docs/)
- **GitHub**: https://github.com/eavelabs-community/py-spring
