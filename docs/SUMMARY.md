# PySpring 文档汇总

## 目录结构总览

### [01-入门指南](01-getting-started/)
- **CLI工具使用** - 项目创建、初始化、诊断工具
- **安装配置** - 环境搭建、依赖安装
- **快速上手** - 项目结构、基本使用方法

### [02-核心概念](02-core-concepts/)
- **IoC容器** - 依赖注入、组件扫描、生命周期管理
- **AOP编程** - 切面编程、方法拦截、运行时代理
- **项目架构** - 模块组织、设计模式

### [03-配置管理](03-configuration/)
- **应用配置** - 配置文件结构、加载机制
- **安全配置** - 认证、授权、密码策略
- **数据库配置** - 连接、缓存、ORM设置
- **日志配置** - 输出、级别、格式设置
- **配置架构** - 三层配置、覆盖机制、环境变量

### [04-功能特性](04-features/)
- **认证授权** - JWT、多字段登录、权限控制
- **安全框架** - 责任链模式、加密保护
- **数据库集成** - ORM、自动初始化、连接池
- **控制器安全** - 访问控制、中间件

### [05-高级主题](05-advanced/)
- **部署策略** - 生产环境、容器化
- **环境配置** - UV工具、虚拟环境
- **安全迁移** - 版本升级、数据迁移

### [06-故障排除](06-troubleshooting/)
- **诊断工具** - 环境检查、配置验证
- **常见问题** - 循环依赖、引用错误、SQL问题
- **登录故障** - 标识符登录、认证问题

### [07-最佳实践](07-best-practices/)
- **项目实践** - 示例修复、代码重构
- **系统维护** - 缓存清理、性能优化

## 推荐学习路径

### 新手路线
1. 从 [01-入门指南](01-getting-started/) 开始
2. 了解 [02-核心概念](02-core-concepts/) 中的IoC容器
3. 学习 [03-配置管理](03-configuration/) 基础配置
4. 查阅 [04-功能特性](04-features/) 了解框架功能

### 进阶路线
1. 深入 [02-核心概念](02-core-concepts/) 中的AOP
2. 掌握 [03-配置管理](03-configuration/) 的配置架构
3. 学习 [04-功能特性](04-features/) 的认证授权
4. 参考 [07-最佳实践](07-best-practices/) 优化项目

### 故障处理路线
1. 使用 [06-故障排除](06-troubleshooting/) 的诊断工具
2. 查看对应问题分类的解决方案
3. 参考最佳实践避免同类问题

## 核心功能摘要

### IoC容器 (控制反转)
- 自动组件扫描和依赖注入
- 循环依赖检测和预防
- 启动缓存优化性能
- 单例和原型模式支持

### AOP (面向切面编程)
- 运行时动态代理
- 方法拦截和增强
- 前置、后置、环绕通知
- 正则表达式切入点匹配

### 安全体系
- JWT Token认证
- 多字段标识符登录
- 责任链认证模式
- RBAC权限控制
- 全链路加密

### 配置系统
- 三层配置架构 (框架默认/用户配置/环境变量)
- YAML配置格式支持
- 深度合并机制
- 配置缓存优化

## 常见配置示例

### 安全配置示例
```yaml
authentication:
  jwt:
    secret_key: ${JWT_SECRET_KEY:your-secret-key-here}
    access_token_expire: 3600
    refresh_token_expire: 2592000
  identifier_fields:
    - "user_id"
    - "username"
    - "email"
    - "phone"
```

### 数据库配置示例
```yaml
database:
  postgresql:
    host: localhost
    port: 5432
    database: myapp
    username: user
    password: ${POSTGRES_PASSWORD:password}
```

### 容器配置示例
```yaml
container:
  scan_cache: true
  lazy_loading: true
scan:
  packages:
    - app.services
    - app.controllers
    - app.repositories
```

## 快捷参考

### 常用CLI命令
- `pyspring init` - 初始化新项目
- `pyspring diagnose` - 诊断环境问题
- `pyspring uv setup` - 设置UV环境

### 依赖注入
- `@Component` - 注册组件
- `@Service` - 注册服务
- `@Repository` - 注册仓库
- 构造函数类型提示自动注入

### 认证装饰器
- `require_authentication_from_token` - 强制认证
- `permission_dependency("permission")` - 权限检查
- `role_dependency("role")` - 角色检查

## 附录

- [术语表](GLOSSARY.md) - 框架术语解释
- [API参考](API.md) - 接口和类说明
- [版本历史](../CHANGELOG.md) - 更新记录
- [许可证](../LICENSE) - 使用许可