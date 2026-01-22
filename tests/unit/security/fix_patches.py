import re

# 读取文件
with open('test_decorators.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换模式
old_pattern = r"        with patch\('pyspring\.security\.authorization\.decorators\.require\.ApplicationContext'\) as mock_ctx:\n            mock_ctx\.get_by_type\.return_value = mock_permission_service"

new_text = """        # Mock ApplicationContext.get_instance().get_by_type()
        with patch('pyspring.security.authorization.decorators.require.ApplicationContext.get_instance') as mock_get_instance:
            mock_ctx = MagicMock()
            mock_ctx.get_by_type.return_value = mock_permission_service
            mock_get_instance.return_value = mock_ctx"""

# 替换
content = re.sub(old_pattern, new_text, content)

# 写回文件
with open('test_decorators.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"替换完成")
