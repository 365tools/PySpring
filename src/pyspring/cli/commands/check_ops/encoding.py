"""
PySpring Encoding Checker Command
"""
import os
import sys
from typing import List, Tuple

from pyspring.cli.component.files.ignore import get_ignore_list
from pyspring.cli.core.ui import (
    print_title, print_file_header, print_issue, print_summary,
    print_info, print_success
)


def collect_text_files(base_path: str) -> List[str]:
    """Collect all text files to check"""
    extensions = {'.py', '.md', '.txt', '.yaml', '.yml', '.toml', '.json', '.ini', '.cfg', '.xml', '.html', '.css', '.js', '.ts'}
    text_files = []

    abs_base = os.path.abspath(base_path)
    if not os.path.exists(abs_base):
        return []

    ignored_dirs = get_ignore_list(os.getcwd())

    if os.path.isfile(abs_base):
        return [abs_base]

    for root, dirs, files in os.walk(abs_base):
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.endswith('.egg-info')]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                text_files.append(os.path.join(root, file))

    return sorted(text_files)


def detect_encoding_issue(file_path: str) -> Tuple[bool, str, str, int, str]:
    """
    Detect file encoding issues
    Returns: (is_issue, issue_type, original_encoding, line_number, context_snippet)
    issue_type: 'BOM', 'Non-UTF8', None
    """
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()

        # Check BOM
        if raw.startswith(b'\xef\xbb\xbf'):
            return True, 'BOM', 'utf-8-sig', 1, ""

        # Try decode as utf-8
        try:
            content = raw.decode('utf-8')
            # Check for Unicode Replacement Character (indicating previous corruption)
            if '\ufffd' in content:
                # Find line number
                idx = content.find('\ufffd')
                line_no = content.count('\n', 0, idx) + 1

                # Get context snippet
                start = max(0, idx - 15)
                end = min(len(content), idx + 15)
                snippet = content[start:end].replace('\n', ' ').strip()
                return True, 'Corrupted (U+FFFD)', 'utf-8', line_no, f"...{snippet}..."
            return False, None, 'utf-8', 0, ""
        except UnicodeDecodeError:
            # Try to guess common encodings (simple fallback)
            # For Windows users in China, GBK is most common fallback
            try:
                raw.decode('gbk')
                return True, 'Non-UTF8', 'gbk', 1, ""
            except UnicodeDecodeError:
                # If failed, treat as unknown binary or mixed
                return True, 'Garbled/Unknown', 'unknown', 1, ""

    except Exception:
        return False, None, 'error', 0, ""


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
        # print_error(f"Failed to convert: {e}") # Handled by caller
        return False


def run_check_encoding(args):
    """Run encoding check command"""
    target_dir = os.path.abspath(args.target)
    do_fix = args.fix

    print_title(f"Checking Encoding: {target_dir}")
    if do_fix:
        print_info("Auto-fix enabled: Will convert files to UTF-8 (no BOM)")

    files = collect_text_files(target_dir)
    total = len(files)
    issues = 0
    fixed = 0

    print_info(f"Scanning {total} files...")

    for i, file_path in enumerate(files, 1):
        is_issue, issue_type, enc, line_no, context = detect_encoding_issue(file_path)

        if is_issue:
            issues += 1
            print_file_header(file_path)
            
            msg = f"{issue_type} ({enc})"
            if context:
                msg += f" - Context: {context}"
                
            level = 'error'

            if do_fix:
                if 'Corrupted' in str(issue_type):
                    print_issue(str(line_no), f"{msg} -> Cannot auto-fix: File contains replacement characters (). Manual repair required.", file_path, level='error')
                elif convert_to_utf8(file_path, enc, issue_type == 'BOM'):
                    print_issue(str(line_no), f"{msg} -> Fixed: UTF-8", file_path, level='success')
                    fixed += 1
                else:
                    print_issue(str(line_no), f"{msg} -> Failed to fix", file_path, level='error')
            else:
                print_issue(str(line_no), msg, file_path, level='error')

    print_summary(issues, issues, fixed, fixable=not do_fix)

    if fixed > 0:
        print()
        print_title("Next Steps")
        print_success("Encoding fixed. Reload modified files in your editor if they are open.")
        
    if issues > fixed:
        sys.exit(1)
