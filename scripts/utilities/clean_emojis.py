#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量清理 security 模块中的 emoji"""

from pathlib import Path

# Emoji 映射规则
EMOJI_MAPPING = {
    '🔑': '[Auth]',
    '✅': '[Success]',
    '🚨': '[Error]',
    '⚠️': '[Warning]',
    '🚀': '[Init]',
    '📋': '[Info]',
    '💾': '[DB]',
    '🔐': '[Security]',
    '🔒': '[Lock]',
    '🔓': '[Unlock]',
    '⭐': '[Star]',
    '🎯': '[Target]',
    '📝': '[Note]',
    '💡': '[Tip]',
    '🛡️': '[Shield]',
    '🔍': '[Debug]',
    '⚡': '[Fast]',
    '🎉': '[Done]',
    '✨': '[New]',
    '🔥': '[Hot]',
    'ℹ️': '[Info]',
}


def remove_emojis_from_file(file_path: Path) -> bool:
    """
    从文件中删除所有 emoji，替换为纯文本标记
    
    Returns:
        True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 替换所有 emoji
        for emoji, replacement in EMOJI_MAPPING.items():
            content = content.replace(emoji, replacement)

        # 通用 emoji 清理（如果有遗漏的）
        # content = re.sub(r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s]', '', content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"❌ 处理文件失败: {file_path}\n   错误: {e}")
        return False


def main():
    """批量清理 security 模块"""
    security_path = Path(r'd:\Project\PycharmProjects\PySpring\src\pyspring\security')

    if not security_path.exists():
        print(f"❌ 路径不存在: {security_path}")
        return

    py_files = list(security_path.rglob('*.py'))
    modified_count = 0

    print(f"开始清理 {len(py_files)} 个文件...")
    print("=" * 60)

    for file_path in py_files:
        if remove_emojis_from_file(file_path):
            modified_count += 1
            print(f"✓ 已修复: {file_path.relative_to(security_path)}")

    print("=" * 60)
    print(f"清理完成！共修复 {modified_count} 个文件")


if __name__ == '__main__':
    main()
