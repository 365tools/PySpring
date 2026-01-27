# PySpring FAQ 与技术文档

本目录包含PySpring框架的常见问题解答、技术指南和故障排查文档。

## 📁 目录结构

### 🔐 [authentication](./authentication/) - 认证相关

- [identifier-login-guide.md](./authentication/identifier-login-guide.md) - Identifier登录功能使用指南
- [IDENTIFIER_LOGIN_IMPLEMENTATION_SUMMARY.md](./authentication/IDENTIFIER_LOGIN_IMPLEMENTATION_SUMMARY.md) - 登录功能实现总结
- [IDENTIFIER_FIELDS_CONFIGURATION_GUIDE.md](./authentication/IDENTIFIER_FIELDS_CONFIGURATION_GUIDE.md) - 登录字段配置指南
- [IDENTIFIER_FIELDS_CONFIG_IMPROVEMENT_SUMMARY.md](./authentication/IDENTIFIER_FIELDS_CONFIG_IMPROVEMENT_SUMMARY.md) - 字段配置改进总结

### ⚙️ [configuration](./configuration/) - 配置管理

- [CONFIG_ARCHITECTURE_FIX_SUMMARY.md](./configuration/CONFIG_ARCHITECTURE_FIX_SUMMARY.md) - 配置架构修复总结
- [CONFIG_MERGE_FIX_REPORT.md](./configuration/CONFIG_MERGE_FIX_REPORT.md) - 配置合并修复报告
- [CONFIG_REFACTORING_CHECKLIST.md](./configuration/CONFIG_REFACTORING_CHECKLIST.md) - 配置重构检查清单

### 🏗️ [ioc](./ioc/) - IoC容器与依赖注入

- [IOC_OPTIMIZATION_ANALYSIS.md](./ioc/IOC_OPTIMIZATION_ANALYSIS.md) - IoC容器优化方案分析
- [REFACTORING_IOC_PATTERN.md](./ioc/REFACTORING_IOC_PATTERN.md) - IoC模式重构
- [ANNOTATION_REFACTORING_SUMMARY.md](./ioc/ANNOTATION_REFACTORING_SUMMARY.md) - 注解重构总结

### 🔧 [troubleshooting](./troubleshooting/) - 故障排查

- [CACHE_CLEANUP_GUIDE.md](./troubleshooting/CACHE_CLEANUP_GUIDE.md) - 缓存清理指南
- [CONDITIONAL_BEAN_BUG_FIX_REPORT.md](./troubleshooting/CONDITIONAL_BEAN_BUG_FIX_REPORT.md) - 条件Bean bug修复
- [EXCEPTION_HANDLER_PROJECT_ROOT_FIX.md](./troubleshooting/EXCEPTION_HANDLER_PROJECT_ROOT_FIX.md) - 异常处理器路径修复
- [PYJWT_EXCEPTION_FIX_REPORT.md](./troubleshooting/PYJWT_EXCEPTION_FIX_REPORT.md) - PyJWT异常修复
- [TEMPLATE_FIX_REPORT.md](./troubleshooting/TEMPLATE_FIX_REPORT.md) - 模板修复报告
- [FOREIGN_KEY_REMOVAL_REPORT.md](./troubleshooting/FOREIGN_KEY_REMOVAL_REPORT.md) - 外键移除报告
- [REMOVE_FOREIGN_KEY_ANALYSIS.md](./troubleshooting/REMOVE_FOREIGN_KEY_ANALYSIS.md) - 外键移除分析
- [SECURITY_CLEANUP_EXECUTION_REPORT.md](./troubleshooting/SECURITY_CLEANUP_EXECUTION_REPORT.md) - 安全模块清理执行报告
- [SECURITY_DEEP_ANALYSIS_REPORT.md](./troubleshooting/SECURITY_DEEP_ANALYSIS_REPORT.md) - 安全模块深度分析
- [SECURITY_THOROUGH_CLEANUP_REPORT.md](./troubleshooting/SECURITY_THOROUGH_CLEANUP_REPORT.md) - 安全模块彻底清理报告
- [IDENTIFIER_LOGIN_TROUBLESHOOTING.md](./troubleshooting/IDENTIFIER_LOGIN_TROUBLESHOOTING.md) - Identifier登录故障排查

### 📖 [guides](./guides/) - 使用指南

- [EXAMPLE_FIX_GUIDE.md](./guides/EXAMPLE_FIX_GUIDE.md) - 示例项目修复指南
- [EXAMPLE_TEMPLATE_JWT_REFACTOR.md](./guides/EXAMPLE_TEMPLATE_JWT_REFACTOR.md) - JWT重构示例

## 🚀 快速导航

### 常见问题

**Q: 如何使用identifier字段进行登录？**  
A: 查看 [identifier-login-guide.md](./authentication/identifier-login-guide.md)

**Q: 如何优化IoC容器性能？**  
A: 查看 [IOC_OPTIMIZATION_ANALYSIS.md](./ioc/IOC_OPTIMIZATION_ANALYSIS.md)

**Q: 配置文件的架构是什么？**  
A: 查看 [CONFIG_ARCHITECTURE_FIX_SUMMARY.md](./configuration/CONFIG_ARCHITECTURE_FIX_SUMMARY.md)

**Q: 遇到缓存相关问题怎么办？**  
A: 查看 [CACHE_CLEANUP_GUIDE.md](./troubleshooting/CACHE_CLEANUP_GUIDE.md)

### 开发指南

- 了解注解系统：[ANNOTATION_REFACTORING_SUMMARY.md](./ioc/ANNOTATION_REFACTORING_SUMMARY.md)
- 配置管理最佳实践：[CONFIG_REFACTORING_CHECKLIST.md](./configuration/CONFIG_REFACTORING_CHECKLIST.md)
- 示例项目开发：[EXAMPLE_FIX_GUIDE.md](./guides/EXAMPLE_FIX_GUIDE.md)

## 📝 文档规范

所有FAQ文档应遵循以下规范：

1. **清晰的标题**：使用有意义的标题描述问题或主题
2. **问题描述**：简明扼要地描述问题背景
3. **解决方案**：提供详细的解决步骤
4. **代码示例**：包含可运行的代码示例
5. **相关链接**：链接到相关文档或资源

## 🤝 贡献

如果您发现文档有误或有改进建议，欢迎提交PR或Issue。
