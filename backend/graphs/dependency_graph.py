"""
dependency_graph.py — Build a file-level import dependency graph.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx

from backend.parsing.code_unit import CodeUnit, CodeUnitType


@dataclass
class DependencyGraph:
    repo_id: str
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    def build(self, units: list[CodeUnit]) -> "DependencyGraph":
        """Build file→file import edges from MODULE-level CodeUnits."""
        # Map module base-name → file path(s)
        module_map: dict[str, list[str]] = {}
        for u in units:
            if u.unit_type == CodeUnitType.MODULE:
                stem = Path(u.file_path).stem
                module_map.setdefault(stem, []).append(u.file_path)
                self.graph.add_node(u.file_path, language=u.language)

        # Add edges from imports
        for u in units:
            if u.unit_type != CodeUnitType.MODULE:
                continue
            for imp in u.imports:
                # Match last component of "a.b.c" → "c"
                parts = imp.split(".")
                for part in parts:
                    for target in module_map.get(part, []):
                        if target != u.file_path:
                            self.graph.add_edge(u.file_path, target)

        return self

    def dependencies_of(self, file_path: str) -> list[str]:
        return list(self.graph.successors(file_path))

    def dependents_of(self, file_path: str) -> list[str]:
        return list(self.graph.predecessors(file_path))

    def most_imported(self, top_n: int = 10) -> list[tuple[str, int]]:
        """Return files sorted by how many others import them."""
        return sorted(
            [(n, self.graph.in_degree(n)) for n in self.graph.nodes],
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

    def to_dict(self) -> dict:
        return {
            "nodes": [
                {"id": n, **self.graph.nodes[n]}
                for n in self.graph.nodes
            ],
            "edges": [
                {"source": u, "target": v}
                for u, v in self.graph.edges
            ],
        }

    def cluster_by_directory(self) -> dict[str, list[str]]:
        """Group files by top-level directory (useful for UI grouping)."""
        clusters: dict[str, list[str]] = {}
        for node in self.graph.nodes:
            top_dir = node.split("/")[0] if "/" in node else "root"
            clusters.setdefault(top_dir, []).append(node)
        return clusters
