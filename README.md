<div align="center">

# PySpring

**Enterprise-Grade Python Web Framework**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-powered-009688.svg)](https://fastapi.tiangolo.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[English](README.md) | [中文文档](README_CN.md) | [Documentation](docs/) | [Changelog](CHANGELOG.md)

</div>

---

## Overview

**PySpring** is a modern, enterprise-grade Python web framework inspired by Spring Boot's design philosophy. Built on FastAPI, it provides production-ready infrastructure including IoC container, authentication, data access, and
comprehensive logging for building scalable applications.

### Why PySpring?

- **🏗️ Spring-Inspired Architecture** - Familiar concepts for Java developers: IoC, dependency injection, lifecycle management
- **⚡ Production Ready** - Battle-tested patterns for authentication, caching, database connections
- **🔧 Configuration-Driven** - Centralized YAML configuration for all framework components
- **🛡️ Security First** - JWT encryption, RBAC, authentication chains, and flexible whitelisting
- **📦 Modular Design** - Loosely coupled components with clear separation of concerns

---

## Key Features

### IoC Container & Dependency Injection

PySpring provides a powerful IoC container for managing application components and their dependencies.

- **Singleton Service Management** - Unified lifecycle management through `ISingletonService` interface
- **Automatic Dependency Resolution** - Type-based and name-based injection strategies
- **Thread-Safe Initialization** - Guaranteed singleton creation in multi-threaded environments
- **Lazy Loading** - Services instantiated on first use for optimized startup

### Application Lifecycle Management

Extensible startup initialization system based on the Initializer Pattern.

- **Startup Initializers** - Pluggable components for application bootstrap tasks
- **Database Auto-Initialization** - Automatic schema creation on application startup
  - **Incremental Mode** - Safe creation of missing tables only
  - **Full Mode** - Complete schema recreation (development only)
  - **Auto-Detection** - Intelligent SQL script path resolution
- **Shutdown Handlers** - Graceful resource cleanup on application termination

### Security & Authentication

Production-ready security infrastructure with flexible configuration.

- **Authentication Chain** - Composable authentication handlers using chain of responsibility
- **JWT Encryption** - Token payload encryption with Fernet/AES-GCM algorithms
- **RBAC Authorization** - Complete role-based access control system
- **Multi-Device Management** - Device tracking and authentication
- **Flexible Whitelisting** - Exact match, prefix match, and regex pattern support

### Data Access Layer

Unified abstraction for data storage with transparent provider switching.

- **Cache Abstraction** - Seamless Memory/Redis cache switching without code changes
- **Database Support** - PostgreSQL, SQLite with unified interface
- **Connection Pooling** - Automatic management of database and cache connections
- **Configuration-Driven** - All storage settings managed through YAML configuration

### Logging Infrastructure

Structured logging system built on Loguru.

- **Structured Logging** - JSON format support for log aggregation
- **Automatic Rotation** - Size and time-based log file rotation
- **Colored Console Output** - Enhanced development experience
- **Contextual Filters** - Request context tracking and filtering

### Project Scaffolding

Command-line tools for rapid project setup.

- **Standardized Structure** - Generate complete project layout with `pyspring init`
- **Template System** - Customizable code generation templates
- **Automatic Configuration** - JWT keys and environment variables auto-generated
- **Production Ready** - Generated `main.py` includes complete startup logic

---

## Installation

### Prerequisites

- Python 3.12 or higher
- pip or uv package manager

### Install via pip

```bash
pip install pyspring
```

### Install via uv (Recommended for Speed)

[uv](https://github.com/astral-sh/uv) is a blazingly fast Python package manager, 10-100x faster than pip:

```bash
# Install uv (first time only)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment and install PySpring
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1 # Windows
uv pip install pyspring
```

### Install from Source

```bash
git clone https://github.com/365tools/PySpring.git
cd PySpring
pip install -e .
```

For detailed installation instructions, see [Installation Guide](docs/01-getting-started/INSTALLATION_GUIDE.md).

---

## Quick Start

### 1. Initialize Project

Create a new project with standardized structure:

```bash
pyspring init
```

This generates a complete application structure:

```
your-project/
├── app/                       # Application code
│   ├── api/                  # API routes and endpoints
│   ├── models/               # Data models and schemas
│   ├── services/             # Business logic layer
│   └── utils/                # Utility functions
├── config/                    # Configuration files
│   ├── container.yaml        # IoC container configuration
│   ├── logging.yaml          # Logging configuration
│   ├── repositories.yaml     # Database and cache configuration
│   └── security.yaml         # Authentication and authorization
├── scripts/db/               # Database scripts
│   ├── init_incremental.sql  # Safe incremental initialization
│   └── init_full.sql         # Full schema recreation
├── tests/                    # Test suite
├── logs/                     # Log files
├── data/                     # Data directory
├── main.py                   # Application entry point
├── .env                      # Environment variables (auto-generated)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
└── pyproject.toml           # Project metadata and dependencies
```

### 2. Configure Environment

The `.env` file is automatically generated with secure JWT keys. Configure other settings as needed:

```bash
# JWT Configuration (auto-generated)
JWT_SECRET_KEY=<auto-generated-secret>
JWT_ENCRYPTION_KEY=<auto-generated-encryption-key>

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password
POSTGRES_DB=your-database

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Configure Database Auto-Initialization

Edit `config/repositories.yaml`:

```yaml
database:
  initialization:
    enabled: true              # Enable auto-initialization
    mode: incremental          # Use safe incremental mode
    auto_detect: true          # Auto-detect script path
    # script_path: scripts/db/init_incremental.sql  # Or specify manually
```

**Initialization Modes:**

- `incremental`: Safe mode - creates only missing tables, preserves existing data
- `full`: Dangerous mode - drops and recreates all tables (development only)

### 4. Run Application

The generated `main.py` includes complete startup logic:

```bash
uvicorn main:app --reload
```

On startup, the application automatically executes initialization tasks:

```
🔧 [DatabaseInitializer] Starting initialization...
✅ [DatabaseInitializer] Database initialization completed
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Access API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Core Concepts

### IoC Container & Singleton Services

PySpring's core is the **IoC (Inversion of Control) container**, providing dependency injection and singleton lifecycle management:

```python
from pyspring.interfaces.ISingleton import ISingletonService

class UserService(ISingletonService):
    """Singleton service example"""
  
    def __init__(self):
        super().__init__()
        # Initialization logic
  
    async def initialize(self) -> bool:
        """Async initialization hook"""
        # Setup resources
        return True
  
    async def cleanup(self) -> None:
        """Cleanup hook"""
        # Release resources
        pass

# Using the service
from pyspring.ioc.manager import AppContainerManager

container = AppContainerManager()
service = container.get(UserService)
```

**Benefits:**

- 🔒 Thread-safe singleton creation
- ⚡ Lazy initialization on first use
- 🔄 Complete lifecycle management (initialize, cleanup)
- 📦 Automatic dependency resolution

### Application Lifecycle

Manage startup tasks using the **Initializer Pattern**:

```python
from pyspring.interfaces.IStartupInitializer import (
    IStartupInitializer, 
    StartupInitializerManager
)

class CacheWarmupInitializer(IStartupInitializer):
    """Cache warmup initializer"""
  
    async def execute(self) -> bool:
        # Cache warmup logic
        logger.info("Cache warmup completed")
        return True

# Register at application startup
@app.on_event("startup")
async def startup():
    manager = StartupInitializerManager()
    manager.register(DatabaseInitializer())     # Database initialization
    manager.register(CacheWarmupInitializer())  # Cache warmup
    await manager.execute_all()
```

**Features:**

- 🎯 Centralized startup task management
- 📊 Sequential execution with logging
- 🛡️ Error handling and rollback support
- 🔌 Easy to extend

### Authentication Chain

Flexible authentication architecture supporting multiple authentication methods:

```python
# Configure multiple authentication handlers
auth_chain = [
    WhitelistAuthHandler(),  # Whitelist check
    JWTAuthHandler(),        # JWT validation
    RBACAuthHandler(),       # Permission check
]
```

### Unified Configuration

All configuration managed through YAML files with environment variable support:

```yaml
# config/security.yaml
authentication:
  jwt:
    secret_key: ${JWT_SECRET_KEY}
    algorithm: HS256
    access_token_expire_minutes: 30
```

---

## CLI Tools

### Available Commands

```bash
# Initialize new project
pyspring init

# Diagnose installation and import issues
pyspring diagnose

# Advanced initialization options
pyspring init --force          # Overwrite existing files
pyspring init --minimal        # Minimal project structure
pyspring init --skip-env       # Skip .env file generation
```

### Diagnostic Tool

Troubleshoot installation or import issues:

```bash
pyspring diagnose
```

The diagnostic tool checks:

- ✅ Python environment (version, path, virtual environment)
- ✅ PySpring installation status
- ✅ Module import functionality
- ✅ Python search path configuration
- ✅ Provides specific solutions

For detailed troubleshooting, see [Troubleshooting Guide](docs/06-troubleshooting/).

### Template System

All generated files come from customizable templates located in `src/pyspring/templates/`.

**Customizing templates:**

1. Edit source files (e.g., `pyproject.toml`, `examples/main_with_db_init.py`)
2. Run `python tools/sync_templates.py` to sync to template directory
3. Reinstall: `pip install -e .`

---

## Documentation

Complete documentation is available in the [docs/](docs/) directory, organized into six categories:

### 🚀 [Getting Started](docs/01-getting-started/)

- [Installation Guide](docs/01-getting-started/INSTALLATION_GUIDE.md) - Detailed installation and setup
- [Project Initialization](docs/01-getting-started/PROJECT_INIT_GUIDE.md) - Complete `pyspring init` guide
- [Quick Reference](docs/01-getting-started/QUICK_REFERENCE.md) - Command and configuration cheatsheet

### 🏗️ [Core Concepts](docs/02-core-concepts/)

- [IoC Container &amp; Singleton Services](docs/02-core-concepts/IOC_SINGLETON_GUIDE.md) - Dependency injection and lifecycle
- [IoC Container Configuration](docs/02-core-concepts/IOC_CONFIG_GUIDE.md) - Container configuration
- [Project Structure](docs/02-core-concepts/PROJECT_STRUCTURE.md) - Framework architecture

### ⚙️ [Configuration](docs/03-configuration/)

- [Configuration Architecture](docs/03-configuration/CONFIG_ARCHITECTURE.md) - Configuration file organization
- [Application Configuration](docs/03-configuration/APPLICATION_CONFIG_GUIDE.md) - App and server settings
- [Logging Configuration](docs/03-configuration/LOGGING_CONFIG_GUIDE.md) - Logging system setup
- [Data Storage Configuration](docs/03-configuration/REPOSITORIES_CONFIG_GUIDE.md) - Database and cache
- [Security Configuration](docs/03-configuration/SECURITY_CONFIG_GUIDE.md) - Authentication and authorization

### ✨ [Features](docs/04-features/)

- [JWT Encryption](docs/04-features/JWT_ENCRYPTION_GUIDE.md) - Token encryption guide
- [JWT Implementation](docs/04-features/JWT_ENCRYPTION_IMPLEMENTATION.md) - Encryption internals
- [Database Auto-Initialization](docs/04-features/DATABASE_AUTO_INIT.md) - Automatic schema creation
- [Template Management](docs/04-features/TEMPLATE_MANAGEMENT.md) - Template system usage

### 🎓 [Advanced Topics](docs/05-advanced/)

- [Framework Migration](docs/05-advanced/SECURITY_MIGRATION_GUIDE.md) - Migrating from other frameworks
- [Project Integration](docs/05-advanced/INSTALLATION_OTHER_PROJECT.md) - Integrate into existing projects
- [uv Package Manager](docs/05-advanced/SETUP_WITH_UV.md) - Fast installation with uv

### 🔧 [Troubleshooting](docs/06-troubleshooting/)

- [Diagnostic Guide](docs/06-troubleshooting/DIAGNOSE_GUIDE.md) - Using diagnostic tools
- [IDE Configuration](docs/06-troubleshooting/FIX_UNRESOLVED_REFERENCE.md) - Fixing IDE issues
- [SQL Issues](docs/06-troubleshooting/SQL_ISSUES.md) - Database problem solving

---

## Examples

### Complete Application

```python
from fastapi import FastAPI
from pyspring.interfaces.IStartupInitializer import StartupInitializerManager
from pyspring.repositories.db.initializer import DatabaseInitializer

app = FastAPI(title="PySpring Application")

@app.on_event("startup")
async def startup():
    """Execute initialization tasks on application startup"""
    manager = StartupInitializerManager()
    manager.register(DatabaseInitializer())
    await manager.execute_all()

@app.get("/")
async def root():
    return {"message": "Welcome to PySpring!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

More examples available in the [examples/](examples/) directory:

- [Configuration Usage](examples/config_usage_example.py) - Configuration management patterns
- [JWT Encryption](examples/jwt_encryption_example.py) - Token encryption implementation
- [Logging Setup](examples/logging_example.py) - Structured logging configuration

---

## Contributing

Contributions are welcome! We appreciate bug reports, feature requests, and code contributions.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/365tools/PySpring.git
cd PySpring

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linting
black src/
flake8 src/
```

### Contribution Guidelines

- Follow [PEP 8](https://pep8.org/) style guide
- Add tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR

---

## License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

### Copyright Notice

Copyright © 2025 [Yingchun] (365tools)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

**Note:** This project was developed independently during personal time and does not involve any proprietary or confidential information from commercial entities.

---

## Acknowledgments

PySpring is built with inspiration and support from the following outstanding open-source projects:

### Design Inspiration

- **[Spring Boot](https://spring.io/projects/spring-boot)** - Design philosophy, architecture patterns, and IoC container concepts

### Core Framework

- **[FastAPI](https://fastapi.tiangolo.com/)** - High-performance modern Python web framework
- **[Uvicorn](https://www.uvicorn.org/)** - Lightning-fast ASGI server
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation and settings management using Python type annotations
- **[Starlette](https://www.starlette.io/)** - Lightweight ASGI framework/toolkit (FastAPI foundation)

### Security & Authentication

- **[python-jose](https://github.com/mpdavis/python-jose)** - JavaScript Object Signing and Encryption (JOSE) for JWT
- **[Passlib](https://passlib.readthedocs.io/)** - Comprehensive password hashing framework
- **[Cryptography](https://cryptography.io/)** - Cryptographic recipes and primitives

### Database & ORM

- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Powerful SQL toolkit and ORM
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migration tool
- **[asyncpg](https://github.com/MagicStack/asyncpg)** - Fast PostgreSQL database client library
- **[aiosqlite](https://github.com/omnilib/aiosqlite)** - Async support for SQLite

### Caching & Storage

- **[Redis](https://redis.io/)** - In-memory data structure store
- **[redis-py](https://github.com/redis/redis-py)** - Python Redis client

### Logging & Configuration

- **[Loguru](https://github.com/Delgan/loguru)** - Python logging made simple and elegant
- **[PyYAML](https://pyyaml.org/)** - YAML parser and emitter
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - Environment variable management

### Dependency Injection

- **[dependency-injector](https://github.com/ets-labs/python-dependency-injector)** - Dependency injection framework

### Development Tools

- **[pytest](https://pytest.org/)** - Testing framework
- **[Black](https://black.readthedocs.io/)** - Code formatter
- **[mypy](http://mypy-lang.org/)** - Static type checker

We are grateful to all the maintainers and contributors of these projects for their excellent work.

---

## Support & Community

### Getting Help

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/365tools/PySpring/issues)
- **Discussions**: [GitHub Discussions](https://github.com/365tools/PySpring/discussions)

### Reporting Issues

When reporting issues, please include:

- PySpring version (`pip show pyspring`)
- Python version (`python --version`)
- Operating system
- Minimal reproducible example
- Error messages and stack traces

### Feature Requests

Feature requests are welcome! Please:

- Check existing issues first
- Clearly describe the use case
- Explain why it benefits the community

---

<div align="center">

**Build Enterprise-Grade Python Applications with PySpring** 🚀

[Documentation](docs/) • [Examples](examples/) • [Contributing](#contributing) • [License](#license)

</div>
