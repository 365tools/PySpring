"""
PySpring 多包架构测试配置

拆包后每个 starter 是独立包（pyspring-core / pyspring-health / pyspring-web /
pyspring-repositories / pyspring-security），均通过 uv workspace 以 editable
方式安装，测试可直接 import。
"""
import copy
import os
import sys
import pytest

# 确保所有包的 src 目录在 python path（editable 安装下通常已覆盖，此处兜底）
_PACKAGES_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../packages'))
for _pkg in ['pyspring', 'pyspring-core', 'pyspring-health', 'pyspring-web',
             'pyspring-repositories', 'pyspring-security', 'pyspring-cli']:
    _src = os.path.join(_PACKAGES_ROOT, _pkg, 'src')
    if os.path.isdir(_src) and _src not in sys.path:
        sys.path.insert(0, _src)

from pyspring.core.log.providers.loguru.config.manager import LoggingConfigManager
from pyspring.core.log.providers.loguru.services.service import LoguruService
from pyspring.core.ioc.context import ApplicationContext


@pytest.fixture(scope="session", autouse=True)
def disable_loguru_enqueue():
    """测试期间禁用 Loguru 异步日志，避免 Windows 下 pytest capture 句柄错误。"""
    original_get = LoggingConfigManager.get

    def patched_get(self, key, default=None):
        value = original_get(self, key, default)
        if key == 'logging' and isinstance(value, dict):
            value = copy.deepcopy(value)
            if 'advanced' not in value:
                value['advanced'] = {}
            value['advanced']['enqueue'] = False
        return value

    LoggingConfigManager.get = patched_get
    LoguruService._configured = False
    LoguruService()

    yield

    LoggingConfigManager.get = original_get


@pytest.fixture(autouse=True)
def cleanup_ioc_container():
    """每个测试后清理 IoC 容器单例，防止跨测试污染。"""
    yield
    ApplicationContext._instance = None
    ApplicationContext._container = None
