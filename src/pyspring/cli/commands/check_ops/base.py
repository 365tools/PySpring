import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from pyspring.cli.component.files.search import find_files
from pyspring.cli.core.ui import (
    print_title, print_file_header, print_issue,
    print_summary, print_info
)


class BaseChecker(ABC):
    """
    Abstract Base Class for all Check Operations
    Provides standardized file scanning, issue tracking, and reporting.
    """

    def __init__(self, target_path: str, extensions: List[str] = None):
        """
        :param target_path: The root path to scan
        :param extensions: List of file extensions to process (e.g. ['.py']). 
                           If None, processes all non-ignored files.
        """
        self.target_path = os.path.abspath(target_path)
        self.extensions = extensions

        # Stats
        self.total_issues = 0
        self.files_checked_count = 0
        self.files_with_issues_count = 0
        self.resolved_count = 0

        # Internal Storage
        # issues: { file_path: [ {line, msg, level, ...} ] }
        self._issues: Dict[str, List[Dict[str, Any]]] = {}

    def run(self, fix: bool = False, **kwargs) -> bool:
        """
        Execute the check.
        :param fix: Whether to attempt auto-fixing
        :return: True if no critical issues found, False otherwise
        """
        print_title(f"{self.title}: {self.target_path}")

        # 1. Collect Files
        files = self._collect_files()
        if not files:
            print_info("No matching files found to check.")
            return True

        self.files_checked_count = len(files)
        print_info(f"Scanning {self.files_checked_count} file(s)...")

        # 2. Pre-check hook (optional)
        self.pre_check(files, **kwargs)

        # 3. Process each file
        for file_path in files:
            # Clear per-file context if needed
            issues_found = self.check_file(file_path, fix=fix, **kwargs)
            if issues_found:
                self.files_with_issues_count += 1

        # 4. Post-check hook (optional)
        self.post_check(files, **kwargs)

        # 5. Report
        self.print_report(fixable=not fix)

        return self.total_issues == 0

    @property
    @abstractmethod
    def title(self) -> str:
        """The display title for this check"""
        pass

    @abstractmethod
    def check_file(self, file_path: str, fix: bool = False, **kwargs) -> bool:
        """
        Process a single file.
        :return: True if issues were found (and added via add_issue), False otherwise.
        """
        pass

    def pre_check(self, files: List[str], **kwargs):
        """Hook to run before file scanning (e.g. build global index)"""
        pass

    def post_check(self, files: List[str], **kwargs):
        """Hook to run after file scanning (e.g. global analysis like circular dep)"""
        pass

    def _collect_files(self) -> List[str]:
        return find_files(self.target_path, self.extensions)

    def add_issue(self, file_path: str, line: int, message: str, level: str = 'error'):
        """
        Register an issue to be printed. 
        Note: Currently usage prints immediately for CLI feedback, 
        but we also store it for summary/stats.
        """
        if file_path not in self._issues:
            self._issues[file_path] = []
            # Print header only once per file
            print_file_header(file_path)

        self._issues[file_path].append({
            'line': line,
            'message': message,
            'level': level
        })

        # Immediate Output
        print_issue(str(line), message, file_path, level=level)
        self.total_issues += 1

    def print_report(self, fixable: bool = False):
        """Print summary stats"""
        print_summary(
            self.total_issues,
            self.files_with_issues_count,
            self.resolved_count,
            fixable=fixable and self.total_issues > 0
        )
