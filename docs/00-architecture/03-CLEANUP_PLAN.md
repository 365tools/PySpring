# PySpring 清理无用/冗余文件方案（CLEANUP_PLAN）

> 版本：v0.1
> 目的：系统性清理已跟踪的冗余文件、构建产物、缓存与已知死代码。

---

## 一、清理原则

1. **只清理确定无用/冗余**的内容，不误删仍被引用的功能。
2. **先确认引用**（用 `grep`/`git grep` 验证），再删除。
3. **git 层面**：用 `git rm --cached`（保留本地）或 `git rm`（连同本地删除）。
4. **每步可回滚**：清理前确认 git 状态干净可回退。

---

## 二、已跟踪的冗余文件

### 2.1 数据库测试文件（已跟踪但应忽略）

```
data/app.db
```

`.gitignore` 已含 `data/*.db`，但该文件在规则生效前已被 `git add`，故仍被跟踪。

**操作：**
```bash
git rm --cached data/app.db   # 停止跟踪（保留本地文件，若无需保留可加本地删除）
echo "data/app.db" >> .gitignore   # 已在 data/*.db 中，确认即可
```

> ✅ git 检查确认：当前被跟踪的 `.pyc`、`egg-info/`、`build/`、`__pycache__` 数量为 0，无需额外清理。

---

## 三、代码冗余（基于 REFACTORING 文档）

### 3.1 已确认完成的重构（无需重复操作）

根据 `core/REFACTORING_COMPLETE.md`，以下已删除：
- `core/configuration/base.py`（代理转发）
- `core/configuration/manager.py`（无用抽象）
- `core/configuration/registry.py`（重复 IoC）
- `core/configuration/validators.py`（未集成）
- `core/environment/`（重复 ConfigLoader）
- `core/abstracts/interfaces/`（空目录）

### 3.2 待收尾的跨模块迁移

> ⚠️ `REFACTORING_COMPLETE.md` 明确："Core 模块重构已完成，**外部模块更新将在后续单独进行**"。

**检查项：**
- [ ] 搜索旧 API `system_service.get(` 在 security/repositories 中的残留
- [ ] 搜索 `settings = AppSettings()` 全局单例残留
- [ ] 确认所有模块使用新 API：`system_service.settings.xxx`

**命令：**
```bash
cd packages/pyspring
grep -rn "system_service.get\|settings = AppSettings()" src/ --include="*.py"
```

---

## 四、配置职责重复（需收敛）

| 文件 | 状态 | 处理 |
|------|------|------|
| `pyspring/config_manager.py` | 模块级三层配置 | 与 `core/configuration` 合并，保留一个权威入口 |
| `pyspring/ioc/config/loader.py` | IoC 配置加载 | 保留（专用于 IoC 扫描配置） |
| `pyspring/core/configuration/loader.py` | 配置加载器 | 保留为权威 |

**建议**：以 `core/configuration` 为唯一配置加载来源，**直接废弃并删除 `config_manager.py`**，不保留任何薄兼容层。

---

## 五、待确认清理项（需人工确认）

以下因无法确定引用方，列入"待确认"清单，不自动删除：

- [ ] `packages/pyspring/pyspring.egg-info/`（若存在于本地但未跟踪，可删除；git 未跟踪则无需操作）
- [ ] `logs/`（空日志目录，可保留）
- [ ] `examples/*.pyc`（本地字节码，git 未跟踪，可清理）
- [ ] `data/` 下其他非 `.db` 文件

---

## 六、执行顺序与验证

```
1. git rm --cached data/app.db            # 清理跟踪的冗余数据文件
2. grep 确认旧 API 无残留（3.2 清单）
3. 收敛配置重复（第四节）
4. 运行 pyspring check --all 验证无回归
5. git status 复查跟踪文件干净
```

---

## 七、验收标准

- [ ] `git ls-files` 中无 `.pyc`、`egg-info`、`build`、`__pycache__`、`data/*.db`
- [ ] 无 `system_service.get(`、`settings = AppSettings()` 残留
- [ ] 配置系统单一权威入口
- [ ] `pyspring check --all` 通过
