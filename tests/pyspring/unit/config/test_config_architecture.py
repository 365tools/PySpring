"""
测试三层配置架构
验证 ConfigManager 能够正确加载和合并配置：
1. 框架默认配置
2. 用户项目配置
3. 环境变量覆盖
"""
import os
import tempfile
from pathlib import Path

import pytest
import yaml
from pyspring.config_manager import ConfigManager


class TestConfigArchitecture:
    """测试三层配置架构"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每个测试前后清理缓存"""
        ConfigManager.clear_cache()
        yield
        ConfigManager.clear_cache()

    def test_load_framework_defaults_only(self):
        """
        测试场景1：只有框架默认配置（无用户配置）
        应该加载框架默认值
        """
        # 加载安全配置（不提供用户配置目录）
        config = ConfigManager.load_config("security", user_config_dir="/non_existent_dir")

        # 验证加载了框架默认值
        assert config is not None
        assert "authentication" in config
        assert "jwt" in config["authentication"]

        # 验证框架默认的 JWT 配置
        jwt_config = config["authentication"]["jwt"]
        assert jwt_config["algorithm"] == "HS256"
        assert jwt_config["access_token_expire"] == 3600  # 框架默认 1 小时

        # 验证框架默认的密码策略
        assert "password" in config
        assert config["password"]["min_length"] == 8  # 框架默认
        assert config["password"]["require_uppercase"] is True

    def test_user_config_overrides_framework_defaults(self):
        """
        测试场景2：用户配置覆盖框架默认值
        用户配置应该覆盖框架默认值，未配置的项使用框架默认
        """
        # 创建临时用户配置目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建用户配置文件（只覆盖部分值）
            user_config = {
                "authentication": {
                    "jwt": {
                        "access_token_expire": 7200,  # 覆盖为 2 小时
                        "refresh_token_expire": 604800  # 覆盖为 7 天
                    }
                },
                "password": {
                    "min_length": 10,  # 覆盖为 10
                    "require_special": True  # 覆盖为 True
                }
            }

            user_config_file = Path(temp_dir) / "security.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            # 加载配置
            config = ConfigManager.load_config("security", user_config_dir=temp_dir)

            # 验证用户配置已覆盖框架默认
            assert config["authentication"]["jwt"]["access_token_expire"] == 7200  # 用户值
            assert config["authentication"]["jwt"]["refresh_token_expire"] == 604800  # 用户值
            assert config["password"]["min_length"] == 10  # 用户值
            assert config["password"]["require_special"] is True  # 用户值

            # 验证未覆盖的项仍使用框架默认
            assert config["authentication"]["jwt"]["algorithm"] == "HS256"  # 框架默认
            assert config["password"]["require_uppercase"] is True  # 框架默认
            assert config["password"]["require_digits"] is True  # 框架默认

    def test_deep_merge_nested_config(self):
        """
        测试场景3：深度合并嵌套配置
        验证深层嵌套的配置项能正确合并
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 用户只覆盖深层的某一个值
            user_config = {
                "authentication": {
                    "jwt": {
                        "encryption": {
                            "enabled": True  # 只覆盖这一个深层值
                        }
                    }
                }
            }

            user_config_file = Path(temp_dir) / "security.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            config = ConfigManager.load_config("security", user_config_dir=temp_dir)

            # 验证深层覆盖成功
            assert config["authentication"]["jwt"]["encryption"]["enabled"] is True  # 用户值

            # 验证同级其他值保持框架默认
            assert config["authentication"]["jwt"]["encryption"]["algorithm"] == "Fernet"  # 框架默认
            assert config["authentication"]["jwt"]["algorithm"] == "HS256"  # 框架默认
            assert config["authentication"]["jwt"]["access_token_expire"] == 3600  # 框架默认

    def test_environment_variable_overrides(self):
        """
        测试场景4：环境变量覆盖配置
        环境变量应该覆盖用户配置和框架默认
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 用户配置
            user_config = {
                "authentication": {
                    "jwt": {
                        "secret_key": "user_secret",  # 用户配置的密钥
                        "access_token_expire": 7200
                    }
                }
            }

            user_config_file = Path(temp_dir) / "security.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            # 设置环境变量（最高优先级）
            os.environ["JWT_SECRET_KEY"] = "env_secret_key_override"
            os.environ["JWT_ENCRYPTION_KEY"] = "env_encryption_key"

            try:
                config = ConfigManager.load_config("security", user_config_dir=temp_dir)

                # 验证环境变量覆盖了用户配置
                assert config["authentication"]["jwt"]["secret_key"] == "env_secret_key_override"
                assert config["authentication"]["jwt"]["encryption"]["encryption_key"] == "env_encryption_key"

                # 验证用户配置仍然有效（未被环境变量覆盖的部分）
                assert config["authentication"]["jwt"]["access_token_expire"] == 7200
            finally:
                # 清理环境变量
                del os.environ["JWT_SECRET_KEY"]
                del os.environ["JWT_ENCRYPTION_KEY"]

    def test_repositories_config_loading(self):
        """
        测试场景5：数据仓储配置加载
        验证 repositories.yaml 的三层架构
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 用户覆盖数据库类型和部分配置
            user_config = {
                "database": {
                    "type": "postgresql",  # 覆盖框架默认的 auto
                    "postgresql": {
                        "host": "custom-db-host",
                        "database": "my_custom_db"
                    }
                },
                "cache": {
                    "type": "redis"  # 覆盖框架默认的 memory
                }
            }

            user_config_file = Path(temp_dir) / "repositories.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            config = ConfigManager.load_config("repositories", user_config_dir=temp_dir)

            # 验证用户配置覆盖
            assert config["database"]["type"] == "postgresql"
            assert config["database"]["postgresql"]["host"] == "custom-db-host"
            assert config["database"]["postgresql"]["database"] == "my_custom_db"
            assert config["cache"]["type"] == "redis"

            # 验证未覆盖的使用框架默认
            assert config["database"]["postgresql"]["port"] == 5432  # 框架默认
            assert config["cache"]["redis"]["host"] == "localhost"  # 框架默认

    def test_repositories_env_overrides(self):
        """
        测试场景6：数据仓储配置的环境变量覆盖
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            user_config = {
                "database": {
                    "postgresql": {
                        "password": "user_password"
                    }
                },
                "cache": {
                    "redis": {
                        "password": "user_redis_pass"
                    }
                }
            }

            user_config_file = Path(temp_dir) / "repositories.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            # 设置环境变量
            os.environ["POSTGRES_PASSWORD"] = "env_pg_password"
            os.environ["REDIS_PASSWORD"] = "env_redis_password"
            os.environ["MYSQL_PASSWORD"] = "env_mysql_password"

            try:
                config = ConfigManager.load_config("repositories", user_config_dir=temp_dir)

                # 验证环境变量覆盖
                assert config["database"]["postgresql"]["password"] == "env_pg_password"
                assert config["cache"]["redis"]["password"] == "env_redis_password"
                assert config["database"]["mysql"]["password"] == "env_mysql_password"
            finally:
                # 清理环境变量
                del os.environ["POSTGRES_PASSWORD"]
                del os.environ["REDIS_PASSWORD"]
                del os.environ["MYSQL_PASSWORD"]

    def test_config_caching(self):
        """
        测试场景7：配置缓存机制
        验证配置缓存能正常工作
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            user_config = {
                "authentication": {
                    "jwt": {
                        "access_token_expire": 9999
                    }
                }
            }

            user_config_file = Path(temp_dir) / "security.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            # 第一次加载（会缓存）
            config1 = ConfigManager.load_config("security", user_config_dir=temp_dir, use_cache=True)

            # 修改配置文件
            user_config["authentication"]["jwt"]["access_token_expire"] = 8888
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            # 第二次加载（使用缓存，应该仍是旧值）
            config2 = ConfigManager.load_config("security", user_config_dir=temp_dir, use_cache=True)
            assert config2["authentication"]["jwt"]["access_token_expire"] == 9999  # 缓存的旧值

            # 强制重新加载（不使用缓存）
            config3 = ConfigManager.reload_config("security", user_config_dir=temp_dir)
            assert config3["authentication"]["jwt"]["access_token_expire"] == 8888  # 新值

            # 清除缓存后再加载
            ConfigManager.clear_cache()
            config4 = ConfigManager.load_config("security", user_config_dir=temp_dir)
            assert config4["authentication"]["jwt"]["access_token_expire"] == 8888  # 新值

    def test_logging_config_loading(self):
        """
        测试场景8：日志配置加载
        验证 logging.yaml 的三层架构
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 用户配置（开发环境）
            user_config = {
                "logging": {
                    "level": "DEBUG",  # 覆盖框架默认的 INFO
                    "file": {
                        "enabled": True,  # 覆盖框架默认的 False
                        "path": "logs/custom_app.log",
                        "rotation": "100 MB"
                    }
                }
            }

            user_config_file = Path(temp_dir) / "logging.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            config = ConfigManager.load_config("logging", user_config_dir=temp_dir)

            # 验证用户配置覆盖
            assert config["logging"]["level"] == "DEBUG"
            assert config["logging"]["file"]["enabled"] is True
            assert config["logging"]["file"]["path"] == "logs/custom_app.log"
            assert config["logging"]["file"]["rotation"] == "100 MB"

            # 验证未覆盖的使用框架默认
            assert config["logging"]["console"]["enabled"] is True  # 框架默认
            assert config["logging"]["console"]["colorize"] is True  # 框架默认
            assert config["logging"]["file"]["retention"] == "7 days"  # 框架默认

    def test_missing_config_falls_back_to_defaults(self):
        """
        测试场景9：缺失配置文件时降级到框架默认值
        """
        # 加载不存在的配置
        config = ConfigManager.load_config("security", user_config_dir="/non_existent_dir")

        # 应该能正常加载框架默认配置
        assert config is not None
        assert "authentication" in config
        assert config["authentication"]["jwt"]["access_token_expire"] == 3600

    def test_convenience_functions(self):
        """
        测试场景10：便捷加载函数
        """
        from pyspring.config_manager import (
            load_security_config,
            load_repositories_config,
            load_logging_config
        )

        # 测试便捷函数
        security_config = load_security_config()
        assert security_config is not None
        assert "authentication" in security_config

        repositories_config = load_repositories_config()
        assert repositories_config is not None
        assert "database" in repositories_config or "cache" in repositories_config

        logging_config = load_logging_config()
        assert logging_config is not None
        assert "logging" in logging_config

    def test_partial_user_config_preserves_framework_structure(self):
        """
        测试场景11：部分用户配置不破坏框架配置结构
        即使用户只提供很少的配置，也应保持完整的框架结构
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 用户只配置一个值
            user_config = {
                "password": {
                    "min_length": 12
                }
            }

            user_config_file = Path(temp_dir) / "security.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            config = ConfigManager.load_config("security", user_config_dir=temp_dir)

            # 验证框架的完整结构仍然存在
            assert "authentication" in config
            assert "jwt" in config["authentication"]
            assert "providers" in config["authentication"]
            assert "whitelist" in config["authentication"]
            assert "authorization" in config
            assert "password" in config
            assert "session" in config
            assert "security_headers" in config

            # 验证用户覆盖生效
            assert config["password"]["min_length"] == 12

            # 验证其他密码策略使用框架默认
            assert config["password"]["max_length"] == 128
            assert config["password"]["require_uppercase"] is True


class TestConfigManagerEdgeCases:
    """测试 ConfigManager 的边界情况"""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """清理缓存"""
        yield
        ConfigManager.clear_cache()

    def test_empty_user_config_file(self):
        """
        测试空的用户配置文件
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建空配置文件
            user_config_file = Path(temp_dir) / "security.yaml"
            user_config_file.touch()

            config = ConfigManager.load_config("security", user_config_dir=temp_dir)

            # 应该加载框架默认值
            assert config is not None
            assert "authentication" in config

    def test_invalid_yaml_falls_back_gracefully(self):
        """
        测试无效的 YAML 文件能优雅降级
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建无效的 YAML 文件
            user_config_file = Path(temp_dir) / "security.yaml"
            with open(user_config_file, 'w') as f:
                f.write("invalid: yaml: content: [[[")

            # 应该能优雅降级到框架默认值
            config = ConfigManager.load_config("security", user_config_dir=temp_dir)
            assert config is not None
            assert "authentication" in config

    def test_nested_null_values_handled_correctly(self):
        """
        测试嵌套的 null 值能正确处理
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            user_config = {
                "authentication": {
                    "jwt": {
                        "secret_key": None,  # null 值
                        "access_token_expire": 5000
                    }
                }
            }

            user_config_file = Path(temp_dir) / "security.yaml"
            with open(user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(user_config, f)

            config = ConfigManager.load_config("security", user_config_dir=temp_dir)

            # null 值应该被保留（用于从环境变量读取）
            assert config["authentication"]["jwt"]["secret_key"] is None
            assert config["authentication"]["jwt"]["access_token_expire"] == 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
