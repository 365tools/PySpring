# PySpring 测试套件

PySpring 框架的完整测试套件，按功能模块组织。

## 目录结构

```
tests/
├── conftest.py              # Pytest 配置文件
├── run_all_tests.py         # 统一运行所有测试的脚本
├── pyspring/               # PySpring 框架相关测试
│   ├── unit/               # 单元测试
│   │   ├── aop/            # AOP 相关测试
│   │   ├── config/         # 配置相关测试
│   │   ├── ioc/            # IoC 相关测试
│   │   ├── log/            # 日志相关测试
│   │   └── security/       # 安全相关测试
│   ├── ioc/                # IoC 容器集成测试
│   ├── security/           # 安全模块测试
│   └── config/             # 配置模块测试
└── pyspring_cli/           # PySpring CLI 工具相关测试
    └── cli/                # CLI 命令测试
```

## 运行测试

### 运行所有测试

```bash
python -m pytest tests/ -v
```

或使用专用的运行脚本：

```bash
python tests/run_all_tests.py
```

### 运行特定模块的测试

```bash
# 运行单元测试
python -m pytest tests/pyspring/unit/ -v

# 运行 IoC 相关测试
python -m pytest tests/pyspring/ioc/ -v

# 运行安全相关测试
python -m pytest tests/pyspring/security/ -v

# 运行 CLI 相关测试
python -m pytest tests/pyspring_cli/cli/ -v
```

### 运行特定类型的测试

```bash
# 只运行单元测试
python -m pytest tests/pyspring/unit/

# 运行测试并显示覆盖率
python -m pytest tests/ --cov=pyspring

# 运行测试并输出详细信息
python -m pytest tests/ -v --tb=long
```

## 测试类型

### 单元测试 (unit/)
- 装饰器功能测试
- 组件注册测试
- 配置解析测试
- 基础功能测试

### 集成测试 (integration/)
- 模块间协作测试
- 完整功能流程测试

### 功能测试 (security/, ioc/, config/)
- 安全模块功能测试
- IoC 容器功能测试
- 配置系统功能测试

## 配置文件

测试配置文件位于 `tests/pyspring/config/` 目录下，包含各种 YAML 配置文件用于测试不同的配置场景。

## 注意事项

1. 所有测试都应遵循 Pytest 的命名约定 (test_*.py 或 *_test.py)
2. 每个测试应保持独立，不应依赖其他测试的结果
3. 使用 fixtures 进行测试设置和清理
4. 避免在测试中硬编码路径，使用相对路径或 Path 对象