"""
Symbol Indexer for Python Projects
Scans a directory tree and builds a mapping of Symbol Name -> Module Path.
"""
import ast
import os
from collections import defaultdict
from typing import Dict, List, Set

from pyspring.cli.component.files.ignore import get_ignore_list


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self):
        self.definitions = []  # List[str]

    def visit_ClassDef(self, node):
        self.definitions.append(node.name)
        # We don't visit inner classes/functions to keep it top-level
        # self.generic_visit(node) 

    def visit_FunctionDef(self, node):
        self.definitions.append(node.name)

    def visit_AsyncFunctionDef(self, node):
        self.definitions.append(node.name)


class ProjectIndexer:
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        # mapping: symbol -> list of module_paths
        self.index: Dict[str, Set[str]] = defaultdict(set)
        self.scanned = False

    def _get_module_path(self, file_path: str) -> str:
        """Convert file path to dotted module path"""
        # Try to find relative path from likely source roots
        candidates = [self.root_dir]
        src_dir = os.path.join(self.root_dir, 'src')
        if os.path.exists(src_dir):
            candidates.insert(0, src_dir)

        best_rel = None
        for base in candidates:
            if file_path.startswith(base):
                rel = os.path.relpath(file_path, base)
                best_rel = rel
                break

        if not best_rel:
            return ""

        # Remove extension
        if best_rel.endswith('.py'):
            best_rel = best_rel[:-3]

        # Handle __init__
        if best_rel.endswith('__init__'):
            best_rel = best_rel[:-9]  # remove \__init__ or /__init__
            if best_rel.endswith(os.sep):
                best_rel = best_rel[:-1]

        return best_rel.replace(os.path.sep, '.')

    def build_index(self):
        """Scan project and build index"""
        ignored = get_ignore_list(os.getcwd())

        print(f"Indexing symbols in {self.root_dir}...")

        file_count = 0
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ignored and not d.startswith('.')]

            for file in files:
                if not file.endswith('.py'):
                    continue

                file_path = os.path.join(root, file)
                module_path = self._get_module_path(file_path)

                if not module_path:
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source = f.read()

                    tree = ast.parse(source, filename=file_path)
                    visitor = SymbolVisitor()
                    visitor.visit(tree)

                    for symbol in visitor.definitions:
                        self.index[symbol].add(module_path)

                    file_count += 1
                except Exception:
                    # Ignore parsing errors during indexing
                    pass

        self.scanned = True
        print(f"Indexed {len(self.index)} symbols from {file_count} files.")

    def find_symbol(self, name: str) -> List[str]:
        """Find module paths where symbol is defined"""
        if not self.scanned:
            self.build_index()
        return sorted(list(self.index.get(name, [])))
