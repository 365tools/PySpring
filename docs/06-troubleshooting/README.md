# 故障排除 (Troubleshooting)

常见问题诊断和解决方案。

## 📚 文档列表

### 诊断工具

- **[DIAGNOSE_GUIDE.md](DIAGNOSE_GUIDE.md)** - PySpring 诊断工具使用指南
    - `pyspring diagnose` 命令
    - 环境检查
    - 配置验证
    - 依赖检测

- **[IDENTIFIER_LOGIN_TROUBLESHOOTING.md](IDENTIFIER_LOGIN_TROUBLESHOOTING.md)** - 标识符登录故障排除
    - 登录问题诊断
    - 配置验证
    - 常见错误处理

### 常见问题

- **[CIRCULAR_DEPENDENCY.md](CIRCULAR_DEPENDENCY.md)** - 解决循环依赖问题 (v1.0.1)
    - `CircularDependencyError` 的含义
    - 重构代码解耦环状依赖
    - 延迟获取的临时方案

- **[FIX_UNRESOLVED_REFERENCE.md](FIX_UNRESOLVED_REFERENCE.md)** - 解决 IDE "Unresolved reference" 问题
    - PyCharm 配置
    - VS Code 配置
    - 虚拟环境设置
    - Python 解释器配置

- **[SQL_ISSUES.md](SQL_ISSUES.md)** - SQL 相关问题修复指南
    - INSERT 语句问题
    - 字段缺失处理
    - 数据库初始化错误
    - SQL 脚本调试

## 🔍 问题分类

### 环境问题

- Python 版本不兼容
- 依赖包缺失
- 虚拟环境配置错误
- IDE 无法识别包

### 配置问题

- 配置文件路径错误
- YAML 语法错误
- 配置项缺失
- 环境变量未设置

### 数据库问题

- 连接失败
- 表结构初始化错误
- SQL 语句错误
- 字段类型不匹配

### 认证问题

- JWT 配置错误
- Token 验证失败
- 权限配置问题
- 白名单不生效
- 标识符登录问题

## 🛠️ 诊断流程

1. **运行诊断工具**
   ```bash
   pyspring diagnose
   ```

2. **检查配置文件**
    - 验证 YAML 语法
    - 确认配置路径
    - 检查环境变量

3. **查看日志输出**
    - 检查错误堆栈
    - 分析日志信息
    - 定位问题模块

4. **参考相关文档**
    - 查找对应问题的解决方案
    - 检查配置示例
    - 对比正确配置

## 💡 获取帮助

如果文档无法解决你的问题：

1. 查看 [GitHub Issues](https://github.com/365tools/PySpring/issues)
2. 提交新的 Issue（提供详细信息）
3. 加入社区讨论

## 📖 相关文档

- 入门指南：[../01-getting-started/](../01-getting-started/)
- 配置指南：[../03-configuration/](../03-configuration/)
- 高级主题：[../05-advanced/](../05-advanced/)