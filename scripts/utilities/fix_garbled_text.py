#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复文件中的乱码字符"""


def fix_file(file_path):
    """修复指定文件的乱码"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 记录修复前的内容片段
    print(f"修复文件: {file_path}")

    # 替换规则
    replacements = [
        ('刷確化栫櫥录服湇务?', '初始化登录服务'),
        ('安全上下文囩理嗗櫒', '安全上下文管理器'),
        ('刷確化栧畬成?', '初始化完成'),
        (r'查找用户 \(委托经?UserProvider\)', '查找用户 (委托给UserProvider)'),
        ('刷確化設证的郴经?', '初始化认证服务'),
    ]

    modified = False
    for old, new in replacements:
        if old in content:
            print(f"  - 替换: {old[:20]}... -> {new}")
            content = content.replace(old, new)
            modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 文件已修复")
    else:
        print(f"ℹ️  文件无需修复")

    return modified


if __name__ == '__main__':
    files_to_fix = [
        r'd:\Project\PycharmProjects\PySpring\src\pyspring\security\authentication\services\flow\login.py',
        r'd:\Project\PycharmProjects\PySpring\src\pyspring\security\authentication\core\factory.py',
    ]

    total_fixed = 0
    for file_path in files_to_fix:
        try:
            if fix_file(file_path):
                total_fixed += 1
        except Exception as e:
            print(f"❌ 修复失败: {file_path}\n   错误: {e}")

    print(f"\n{'=' * 50}")
    print(f"修复完成！共修复 {total_fixed} 个文件")
