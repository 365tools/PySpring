import copy

import pytest
from pyspring.log.loguru.config.manager import LoggingConfigManager
from pyspring.log.loguru.impl.service import LoguruService


@pytest.fixture(scope="session", autouse=True)
def disable_loguru_enqueue():
    """
    在测试期间强制禁用 Loguru 的 enqueue (异步日志)，
    以避免 Windows 下 pytest capture 导致的 OSError: [WinError 6] 句柄无效。
    此 Fix 通过 MonkeyPatch 拦截配置读取，不修改核心代码。
    """
    # 保存原始方法
    original_get = LoggingConfigManager.get

    # 定义替换方法（显式签名，避免 Mock 参数错乱）
    def patched_get(self, key, default=None):
        # 1. 调用原始逻辑
        value = original_get(self, key, default)

        # 2. 拦截并修改 logging 配置
        if key == 'logging' and isinstance(value, dict):
            # 深拷贝以防污染缓存（虽然在这个场景下污染也不怕）
            value = copy.deepcopy(value)

            if 'advanced' not in value:
                value['advanced'] = {}

            # 核心修改：强制禁用 enqueue
            value['advanced']['enqueue'] = False

        return value

    # 应用 MonkeyPatch
    LoggingConfigManager.get = patched_get

    try:
        # 3. 强制重新初始化 LoguruService
        # 即使它在 import 阶段已经被初始化过（使用了 old config），
        # 我们这里清除 Loguru 的 handler 并强制它用新配置再跑一遍 _setup_logging

        # 重置初始化标志，允许 __init__ 再次执行初始化逻辑
        LoguruService._configured = False

        # 重新实例化会触发 _setup_logging -> 调用我们要的 patched_get
        LoguruService()

        yield

    finally:
        # 还原 MonkeyPatch
        LoggingConfigManager.get = original_get
