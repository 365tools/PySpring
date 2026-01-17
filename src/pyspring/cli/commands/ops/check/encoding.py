"""
PySpring Encoding Checker Command
"""
from typing import Tuple

from pyspring.cli.core.ui import (
    print_title, print_success
)
from .base import BaseChecker


class EncodingChecker(BaseChecker):
    @property
    def title(self) -> str:
        return "Checking Encoding"

    def __init__(self, target_path: str):
        extensions = [
            '.py', '.md', '.txt', '.yaml', '.yml', '.toml', '.json',
            '.ini', '.cfg', '.xml', '.html', '.css', '.js', '.ts'
        ]
        super().__init__(target_path, extensions)

    def check_file(self, file_path: str, fix: bool = False, **kwargs) -> bool:
        is_issue, issue_type, enc, line_no, context = self._detect_issue(file_path)

        if not is_issue:
            return False

        msg = f"{issue_type} ({enc})"
        if context:
            msg += f" - Context: {context}"

        if fix:
            if 'Corrupted' in str(issue_type):
                self.add_issue(file_path, line_no, f"{msg} -> Cannot auto-fix: File contains replacement characters. Manual repair required.", level='error')
            elif self._convert_to_utf8(file_path, enc, issue_type == 'BOM'):
                self.record_fix(file_path, line_no, f"{msg} -> Fixed: UTF-8")
            else:
                self.add_issue(file_path, line_no, f"{msg} -> Fix failed (conversion error)", level='error')
        else:
            self.add_issue(file_path, line_no, msg, level='error')

        return True

    def _detect_issue(self, file_path: str) -> Tuple[bool, str, str, int, str]:
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

    def _convert_to_utf8(self, file_path: str, source_encoding: str, has_bom: bool) -> bool:
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
        except Exception:
            return False

def run_check_encoding(args):
    """Run encoding check command"""
    checker = EncodingChecker(args.target)

    if args.fix:
        # We can perform pre-run logging here if needed, or rely on BaseChecker to print Title
        pass  # BaseChecker prints title

    success = checker.run(fix=args.fix)

    if checker.resolved_count > 0:
        print()
        print_title("Next Steps")
        print_success("Encoding fixed. Reload modified files in your editor if they are open.")

    if not success and checker.resolved_count < checker.total_issues:
        # sys.exit(1)
        pass

    return success
