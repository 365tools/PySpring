# PySpring 测试文档

## 测试文件说明

### 综合测试

- **test_comprehensive.py** - 完整的功能测试套件
    - IoC 容器管理
    - 依赖注入
    - 自动扫描和注册
    - 接口映射
    - 配置管理
    - 启动/关闭生命周期
    - 数据库和缓存服务

### 专项测试

- **test_full_lifecycle.py** - 完整应用生命周期测试
- **test_auto_discover_handlers.py** - 自动发现关闭处理器测试
- **test_auto_discover_initializers.py** - 自动发现启动初始化器测试

### 单元测试

- **test_singleton_simple.py** - 单例模式基础测试
- **test_singleton_refactor.py** - 单例模式重构测试

### 功能测试

- **test_database_initializer.py** - 数据库初始化器测试
- **test_db_init_summary.py** - 数据库初始化总结测试
- **test_init_setup.py** - 初始化设置测试
- **test_main_template.py** - 主模板测试

## 运行测试

### 运行所有测试

```bash
# 使用 pytest
pytest tests/ -v

# 使用测试运行器
python tests/run_tests.py all
```

### 运行综合测试

```bash
pytest tests/test_comprehensive.py -v

# 或
python tests/run_tests.py comprehensive
```

### 运行特定测试

```bash
# 生命周期测试
python tests/run_tests.py lifecycle

# 自动发现测试
python tests/run_tests.py auto-discover
```

### 运行单个测试类

```bash
pytest tests/test_comprehensive.py::TestIoCContainer -v
```

### 运行单个测试方法

```bash
pytest tests/test_comprehensive.py::TestIoCContainer::test_singleton_pattern -v
```

## 测试覆盖率

### 核心功能测试覆盖

- ✅ IoC 容器初始化
- ✅ 单例模式
- ✅ 服务名称生成
- ✅ 自动扫描（Service/Handler/Initializer）
- ✅ 依赖注入
- ✅ 接口映射和实现发现
- ✅ 配置管理（IoC/日志/仓储）
- ✅ 启动初始化器自动发现和执行
- ✅ 关闭处理器自动发现和执行
- ✅ 完整生命周期
- ✅ 数据库服务
- ✅ 缓存服务
- ✅ 安全服务

## 测试环境要求

### 必需

- Python 3.10+
- pytest
- pytest-asyncio

### 可选（用于完整功能测试）

- Redis（缓存测试）
- PostgreSQL（数据库测试）

**注意**: 如果 Redis 或 PostgreSQL 不可用，框架会自动降级到 Memory 缓存和 SQLite 数据库。

## 持续集成

测试设计为可以在 CI/CD 环境中运行，无需外部依赖：

- 缓存服务会自动降级到 Memory
- 数据库会自动降级到 SQLite
- 所有测试都有适当的异常处理

## 测试原则

1. **隔离性**: 每个测试独立运行，不依赖其他测试
2. **可重复性**: 测试结果应该一致
3. **降级友好**: 在缺少外部依赖时能优雅降级
4. **快速执行**: 综合测试套件应在 10 秒内完成
5. **清晰反馈**: 测试失败时提供明确的错误信息

## 添加新测试

### 1. 添加到综合测试

编辑 `test_comprehensive.py`，在相应的测试类中添加新方法：

```python
class TestYourFeature:
    def test_your_functionality(self):
        # 你的测试代码
        assert True
```

### 2. 创建独立测试文件

```python
# tests/test_your_feature.py
import pytest

def test_your_feature():
    # 你的测试代码
    assert True
```

### 3. 异步测试

```python
@pytest.mark.asyncio
class TestAsyncFeature:
    async def test_async_functionality(self):
        result = await some_async_function()
        assert result is not None
```

## 故障排查

### 测试失败常见原因

1. **服务未注册**
    - 确保类名以 Service/Handler/Initializer 结尾
    - 检查类是否在扫描路径中

2. **依赖注入失败**
    - 确保构造函数参数有类型注解
    - 检查依赖服务是否已注册

3. **配置文件缺失**
    - 检查 config/ 目录下的 YAML 文件
    - 运行 `pyspring init` 生成配置

4. **异步测试问题**
    - 确保测试类使用 `@pytest.mark.asyncio`
    - 测试方法需要 `async def`

## 性能基准

在标准开发机器上的预期执行时间：

- 综合测试套件: < 10 秒
- 生命周期测试: < 15 秒（包含真实的服务初始化）
- 单元测试: < 1 秒

## 贡献指南

提交代码前请确保：

1. 所有测试通过
2. 添加了相应的测试用例
3. 测试覆盖率不低于当前水平
4. 遵循测试命名规范
