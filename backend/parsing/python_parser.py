"""
python_parser.py — Parse Python source files using the built-in `ast` module.

Extracts functions, methods, and classes as CodeUnit objects.
"""
from __future__ import annotations
import ast
from pathlib import Path
from typing import Optional

from backend.parsing.code_unit import CodeUnit, CodeUnitType


def _get_docstring(node: ast.AST) -> Optional[str]:
    return ast.get_docstring(node)


def _get_calls(node: ast.AST) -> list[str]:
    """Collect all function/method names called within *node*."""
    calls: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return list(dict.fromkeys(calls))  # deduplicate, preserve order


def _node_source(source_lines: list[str], node: ast.AST) -> str:
    start = node.lineno - 1
    end = node.end_lineno
    return "\n".join(source_lines[start:end])


def _decorators(node) -> list[str]:
    decs = []
    for d in getattr(node, "decorator_list", []):
        if isinstance(d, ast.Name):
            decs.append(d.id)
        elif isinstance(d, ast.Attribute):
            decs.append(d.attr)
    return decs


def parse_python_file(
    repo_id: str,
    rel_path: str,
    source_code: str,
) -> list[CodeUnit]:
    """
    Parse *source_code* and return a list of CodeUnit objects.
    Raises SyntaxError if the file cannot be parsed.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    source_lines = source_code.splitlines()
    units: list[CodeUnit] = []

    # ── Module-level imports ──────────────────────────────────────────── #
    import_lines = [
        ast.get_source_segment(source_code, node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    import_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            import_names.append(node.module)

    # Add a module-level unit (the whole file, for context)
    units.append(CodeUnit(
        repo_id=repo_id,
        file_path=rel_path,
        language="python",
        unit_type=CodeUnitType.MODULE,
        name=Path(rel_path).stem,
        code=source_code[:3000],   # store first 3k chars for module overview
        start_line=1,
        end_line=len(source_lines),
        imports=import_names,
    ))

    # ── Top-level classes ─────────────────────────────────────────────── #
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            class_code = _node_source(source_lines, node)
            class_unit = CodeUnit(
                repo_id=repo_id,
                file_path=rel_path,
                language="python",
                unit_type=CodeUnitType.CLASS,
                name=node.name,
                code=class_code,
                start_line=node.lineno,
                end_line=node.end_lineno,
                docstring=_get_docstring(node),
                decorators=_decorators(node),
            )
            units.append(class_unit)

            # Methods inside the class
            for item in ast.iter_child_nodes(node):
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    units.append(CodeUnit(
                        repo_id=repo_id,
                        file_path=rel_path,
                        language="python",
                        unit_type=CodeUnitType.METHOD,
                        name=item.name,
                        code=_node_source(source_lines, item),
                        start_line=item.lineno,
                        end_line=item.end_lineno,
                        parent_class=node.name,
                        docstring=_get_docstring(item),
                        decorators=_decorators(item),
                        calls=_get_calls(item),
                    ))

        # ── Top-level functions ───────────────────────────────────────── #
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            units.append(CodeUnit(
                repo_id=repo_id,
                file_path=rel_path,
                language="python",
                unit_type=CodeUnitType.FUNCTION,
                name=node.name,
                code=_node_source(source_lines, node),
                start_line=node.lineno,
                end_line=node.end_lineno,
                docstring=_get_docstring(node),
                decorators=_decorators(node),
                calls=_get_calls(node),
            ))

    return units
