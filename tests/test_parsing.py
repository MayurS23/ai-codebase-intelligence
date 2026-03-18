"""
test_parsing.py — Unit tests for the Python parser and chunker.
"""
import pytest
from backend.parsing.python_parser import parse_python_file
from backend.parsing.code_unit import CodeUnitType
from backend.chunking.smart_chunker import chunk_units


SAMPLE_CODE = '''
"""Module docstring."""
import os
from pathlib import Path


def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}"


class AuthService:
    """Handles authentication."""

    def __init__(self):
        self.db = None

    def login(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        token = self._generate_token(username)
        return bool(token)

    def _generate_token(self, username: str) -> str:
        return username + "_token"
'''


def test_parse_functions():
    units = parse_python_file("test_repo", "auth.py", SAMPLE_CODE)
    func_names = [u.name for u in units if u.unit_type == CodeUnitType.FUNCTION]
    assert "greet" in func_names


def test_parse_class():
    units = parse_python_file("test_repo", "auth.py", SAMPLE_CODE)
    class_names = [u.name for u in units if u.unit_type == CodeUnitType.CLASS]
    assert "AuthService" in class_names


def test_parse_methods():
    units = parse_python_file("test_repo", "auth.py", SAMPLE_CODE)
    methods = [u for u in units if u.unit_type == CodeUnitType.METHOD]
    method_names = [m.name for m in methods]
    assert "login" in method_names
    assert "_generate_token" in method_names


def test_method_has_parent_class():
    units = parse_python_file("test_repo", "auth.py", SAMPLE_CODE)
    login = next(u for u in units if u.name == "login")
    assert login.parent_class == "AuthService"


def test_calls_extracted():
    units = parse_python_file("test_repo", "auth.py", SAMPLE_CODE)
    login = next(u for u in units if u.name == "login")
    assert "_generate_token" in login.calls


def test_module_unit_created():
    units = parse_python_file("test_repo", "auth.py", SAMPLE_CODE)
    modules = [u for u in units if u.unit_type == CodeUnitType.MODULE]
    assert len(modules) == 1


def test_chunker_assigns_ids():
    units = parse_python_file("test_repo", "auth.py", SAMPLE_CODE)
    chunked = chunk_units(units)
    for u in chunked:
        assert u.chunk_id is not None


def test_large_unit_split():
    # Must exceed MAX_CHARS (6000) to trigger splitting
    large_code = "def big():\n" + "    some_very_long_variable_name = some_function_call(argument_one, argument_two)\n" * 100
    from backend.parsing.code_unit import CodeUnit, CodeUnitType
    unit = CodeUnit(
        repo_id="r", file_path="f.py", language="python",
        unit_type=CodeUnitType.FUNCTION, name="big",
        code=large_code, start_line=1, end_line=200,
    )
    result = chunk_units([unit])
    assert len(result) > 1
    assert all("[part" in u.name for u in result)
