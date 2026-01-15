"""
PySpring Encoding Checker Command
"""
import os
import sys
from typing import List, Tuple

from pyspring.cli.core.ui import print_section


def collect_text_files(base_path: str) -> List[str]:
    """收集所有需要检查的文本文件"""
    extensions = {'.py', '.md', '.txt', '.yaml', '.yml', '.toml', '.json', '.ini', '.cfg', '.xml', '.html', '.css', '.js', '.ts'}
    text_files = []

    abs_base = os.path.abspath(base_path)
    if not os.path.exists(abs_base):
        return []

    ignored_dirs = {'.git', '.venv', 'venv', '__pycache__', 'build', 'dist', '.idea', '.vscode', 'node_modules'}

    if os.path.isfile(abs_base):
        return [abs_base]

    for root, dirs, files in os.walk(abs_base):
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.endswith('.egg-info')]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                text_files.append(os.path.join(root, file))

    return sorted(text_files)


def detect_encoding_issue(file_path: str) -> Tuple[bool, str, str]:
    """
    检测文件编码问题
    Returns: (is_issue, issue_type, original_encoding)
    issue_type: 'BOM', 'Non-UTF8', None
    """
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()

        # Check BOM
        if raw.startswith(b'\xef\xbb\xbf'):
            return True, 'BOM', 'utf-8-sig'

        # Try decode as utf-8
        try:
            content = raw.decode('utf-8')
            # Check for Unicode Replacement Character (indicating previous corruption)
            if '\ufffd' in content:
                return True, 'Corrupted (U+FFFD)', 'utf-8'
            return False, None, 'utf-8'
        except UnicodeDecodeError:
            # Try to guess common encodings (simple fallback)
            # For Windows users in China, GBK is most common fallback
            try:
                raw.decode('gbk')
                return True, 'Non-UTF8', 'gbk'
            except UnicodeDecodeError:
                # If failed, treat as unknown binary or mixed
                return True, 'Garbled/Unknown', 'unknown'

    except Exception:
        return False, None, 'error'


def convert_to_utf8(file_path: str, source_encoding: str, has_bom: bool) -> bool:
    """Convert file to clean utf-8"""
    try:
        read_encoding = 'utf-8-sig' if has_bom else source_encoding
        if source_encoding == 'unknown':
            # Try 'mbcs' (system default on windows) or 'latin-1' as last resort
            read_encoding = 'mbcs'

        with open(file_path, 'r', encoding=read_encoding, errors='replace') as f:
            content = f.read()

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"    Failed to convert: {e}")
        return False


def run_check_encoding(args):
    """运行编码检查命令"""
    target_dir = os.path.abspath(args.target)
    do_fix = args.fix

    print_section(f"Checking encoding in: {target_dir}")
    if do_fix:
        print("Auto-fix enabled: Will convert files to UTF-8 (no BOM)")

    files = collect_text_files(target_dir)
    total = len(files)
    issues = 0
    fixed = 0

    print(f"\nScanning {total} files...\n")

    for i, file_path in enumerate(files, 1):
        rel_path = os.path.relpath(file_path, os.getcwd())
        is_issue, issue_type, enc = detect_encoding_issue(file_path)

        if is_issue:
            issues += 1
            status_icon = "❌"
            msg = f"{issue_type} ({enc})"

            if do_fix:
                if convert_to_utf8(file_path, enc, issue_type == 'BOM'):
                    status_icon = "✅"
                    msg = f"Fixed: {issue_type} -> UTF-8"
                    fixed += 1
                else:
                    status_icon = "⚠️"
                    msg = f"Failed to fix: {issue_type}"

            print(f"[{i}/{total}] {status_icon} {rel_path}")
            print(f"    Status: {msg}")
            # 如果是只检查不修复， 或者修复失败了， 打印完整路径方便跳转
            if not do_fix or "Failed" in msg:
                print(f"    File: {file_path}")

        # Optional: Verbose mode could print all files

    print("\n" + "=" * 50)
    print("Encoding Check Summary")
    print("=" * 50)
    print(f"Total Files: {total}")
    print(f"Issues Found: {issues}")

    if do_fix:
        print(f"Fixed Files:  {fixed}")
        if issues > fixed:
            print(f"Remaining:    {issues - fixed}")

    if issues > fixed:
        sys.exit(1)
    else:
        print("\nAll files are clean UTF-8!")
