"""
code_unit.py — Core data model representing a parsed unit of code.

A CodeUnit is the fundamental atom of this system. Every function,
class, or module extracted from source files becomes a CodeUnit.
This model travels through parsing → chunking → embedding → storage.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CodeUnitType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"       # whole-file level
    IMPORT_BLOCK = "import_block"


@dataclass
class CodeUnit:
    """A single semantic unit of code extracted from a source file."""

    # Identity
    repo_id: str            # slug of the repository being analysed
    file_path: str          # relative path inside the repo
    language: str           # "python", "javascript", …

    # Code content
    unit_type: CodeUnitType
    name: str               # function/class name; filename for MODULE
    code: str               # raw source text of this unit
    start_line: int
    end_line: int

    # Optional enrichment
    parent_class: Optional[str] = None      # set for methods
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)   # for MODULE units
    calls: list[str] = field(default_factory=list)     # functions this unit calls

    # Embedding
    embedding: Optional[list[float]] = None
    chunk_id: Optional[str] = None          # assigned after chunking

    # ------------------------------------------------------------------ #
    def metadata_dict(self) -> dict:
        """Return a flat dict safe to store as ChromaDB metadata."""
        return {
            "repo_id": self.repo_id,
            "file_path": self.file_path,
            "language": self.language,
            "unit_type": self.unit_type.value,
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "parent_class": self.parent_class or "",
            "docstring": (self.docstring or "")[:500],   # truncate for metadata
            "calls": ",".join(self.calls),
        }

    def to_embed_text(self) -> str:
        """
        Build the text that gets embedded.
        Prepend a natural-language header so the model understands context.
        """
        header_parts = [
            f"File: {self.file_path}",
            f"Language: {self.language}",
            f"Type: {self.unit_type.value}",
            f"Name: {self.name}",
        ]
        if self.parent_class:
            header_parts.append(f"Class: {self.parent_class}")
        if self.docstring:
            header_parts.append(f"Docstring: {self.docstring}")

        header = "\n".join(header_parts)
        return f"{header}\n\n{self.code}"
