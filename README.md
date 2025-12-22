# PySpring 🚀

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)

**PySpring** 是一款受 SpringBoot 启发、基于 FastAPI 构建的高性能 Python Web 开发脚手架。它通过 **IoC (控制反转)**、**自动装配** 以及 **模块化抽象**，解决了 Python 开发中配置繁琐、耦合度高的问题。

---

## ✨ 核心特性

- **🧩 自动装配 (Auto-Configuration)**
  基于装饰器、指定包路径实现零配置启动，自动扫描并注册依赖模块。
- **📦 IoC 容器与依赖注入**
  内置高性能 Bean 容器，支持 @Annotated、@Depends 等注解，实现组件解耦。
- **🛡️ 模块化 Auth 认证**
  内置基于 RBAC 的权限模型，支持多设备登录关联与 Token 自动续期。
- **💾 智能缓存抽象层**
  统一缓存层，支持 Memory 与 Redis 等的透明切换，业务代码无需改动。
- **🗄️ 多数据库动态适配**
  统一访问层，完美适配 PostgreSQL 与 SQLite 等，支持自动化连接池管理。

---

## 🛠️ 安装

`pip install pyspring-core`

---

## 🚀 快速开始

### 1. 定义组件
```
from pyspring import Component

@Component
class DataService:
    def fetch_data(self):
        return {"status": "success", "data": "PySpring is running"}
```

### 2. 自动注入路由

```
from pyspring import FastBootApp, Autowired

@router.post("/login", response_model=HttpResponse[dict])
async def login(
        request: LoginRequest,
        login_service: Annotated[LoginService, Depends(lambda: AppContainerManager.service(LoginService))],
) -> JSONResponse:
    """
    用户登录
    
    Args:
        request: 登录请求（用户ID/邮箱和密码）
        login_service: 登录服务
        
    Returns:
        包含 access_token、refresh_token 和用户信息的响应
    """
    pass
```

### 3. 启动应用
```
if __name__ == "__main__":
    FastBootApp.run(port=8000)
```

---

## ⚖️ 开源协议与声明

本项目采用 Apache License 2.0 协议。

**版权声明：**
* 本项目由作者利用个人业余时间独立开发，不涉及任何商业公司机密或专有资源。
* 任何组织或个人均可根据 Apache 2.0 协议免费使用、修改及分发本项目。

Copyright (c) 2025 [Yingchun] (365tools)
