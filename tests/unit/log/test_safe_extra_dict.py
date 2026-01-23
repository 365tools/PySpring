"""
测试 SafeExtraDict 功能

验证日志系统能够安全处理任何缺失的 extra 字段
"""
import pytest
from pyspring.log.providers.loguru.services.service import _SafeExtraDict


class TestSafeExtraDict:
    """测试 SafeExtraDict 类"""

    def test_normal_dict_operations(self):
        """测试正常的字典操作"""
        d = _SafeExtraDict()

        # 设置和获取值
        d["key1"] = "value1"
        assert d["key1"] == "value1"

        # 使用 get 方法
        assert d.get("key1") == "value1"
        assert d.get("nonexistent", "default") == "default"

    def test_missing_key_returns_empty_string(self):
        """测试访问不存在的键返回空字符串"""
        d = _SafeExtraDict()

        # 访问不存在的键应该返回空字符串而不是抛出 KeyError
        assert d["nonexistent"] == ""
        assert d["session_id"] == ""
        assert d["request_id"] == ""
        assert d["any_custom_field"] == ""

    def test_no_keyerror_raised(self):
        """测试不会抛出 KeyError"""
        d = _SafeExtraDict()

        # 这些操作不应该抛出 KeyError
        try:
            value = d["nonexistent_key"]
            assert value == ""
        except KeyError:
            pytest.fail("SafeExtraDict should not raise KeyError")

    def test_preserves_existing_values(self):
        """测试保留已存在的值"""
        d = _SafeExtraDict({"existing": "value", "session_id": "sess123"})

        # 已存在的值应该被保留
        assert d["existing"] == "value"
        assert d["session_id"] == "sess123"

        # 不存在的键返回空字符串
        assert d["nonexistent"] == ""

    def test_can_update_values(self):
        """测试可以更新值"""
        d = _SafeExtraDict()

        # 初始为空
        assert d["key"] == ""

        # 设置值
        d["key"] = "value"
        assert d["key"] == "value"

        # 更新值
        d["key"] = "new_value"
        assert d["key"] == "new_value"

    def test_in_operator(self):
        """测试 in 操作符"""
        d = _SafeExtraDict({"existing": "value"})

        assert "existing" in d
        assert "nonexistent" not in d

    def test_keys_values_items(self):
        """测试 keys(), values(), items() 方法"""
        d = _SafeExtraDict({"key1": "value1", "key2": "value2"})

        assert set(d.keys()) == {"key1", "key2"}
        assert set(d.values()) == {"value1", "value2"}
        assert set(d.items()) == {("key1", "value1"), ("key2", "value2")}

    def test_format_string_usage(self):
        """测试在格式字符串中使用"""
        d = _SafeExtraDict({"session_id": "sess123"})

        # 存在的字段
        result = "{session_id} | {user_id}".format(**d)
        assert result == "sess123 | "

        # 不存在的字段显示为空
        d2 = _SafeExtraDict()
        result2 = "{session_id} | {request_id} | {any_field}".format(**d2)
        assert result2 == " |  | "


class TestSafeExtraDictIntegration:
    """集成测试：模拟实际日志场景"""

    def test_loguru_format_simulation(self):
        """模拟 Loguru 日志格式字符串"""
        # 模拟一个日志记录
        record = {
            "time": "2026-01-23 10:30:45",
            "level": "INFO",
            "message": "User logged in",
            "extra": _SafeExtraDict({"session_id": "sess_abc123"})
        }

        # 模拟格式化（包含存在和不存在的字段）
        format_str = "{time} | {level} | {session_id} | {user_id} | {request_id} | {message}"
        result = format_str.format(
            time=record["time"],
            level=record["level"],
            message=record["message"],
            **record["extra"]
        )

        # 存在的字段显示实际值，不存在的字段显示为空
        expected = "2026-01-23 10:30:45 | INFO | sess_abc123 |  |  | User logged in"
        assert result == expected

    def test_dynamic_field_binding(self):
        """测试动态字段绑定"""
        # 初始状态：空字典
        extra = _SafeExtraDict()

        # 格式字符串包含多个字段
        format_str = "{session_id} | {user_id} | {custom_field}"

        # 第一次：所有字段都为空
        result1 = format_str.format(**extra)
        assert result1 == " |  | "

        # 绑定一个字段
        extra["session_id"] = "sess123"
        result2 = format_str.format(**extra)
        assert result2 == "sess123 |  | "

        # 绑定更多字段
        extra["user_id"] = "user456"
        extra["custom_field"] = "custom_value"
        result3 = format_str.format(**extra)
        assert result3 == "sess123 | user456 | custom_value"

    def test_mixed_fields(self):
        """测试混合使用预定义和自定义字段"""
        extra = _SafeExtraDict({
            "file_relative": "src/service.py",
            "session_id": "sess123"
        })

        # 使用各种字段的格式
        format_str = "{file_relative} | {session_id} | {custom1} | {custom2}"
        result = format_str.format(**extra)

        assert result == "src/service.py | sess123 |  | "


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
