"""
call_graph.py — Build a directed function call graph from parsed CodeUnits.

Graph: node = "file::function_name", edge A→B means A calls B.
Uses NetworkX DiGraph for traversal, cycle detection, and path finding.
"""
from __future__ import annotations
from dataclasses import dataclass, field

import networkx as nx

from backend.parsing.code_unit import CodeUnit, CodeUnitType


@dataclass
class CallGraph:
    repo_id: str
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    # ── Build ──────────────────────────────────────────────────────────── #
    def build(self, units: list[CodeUnit]) -> "CallGraph":
        """Populate the graph from a list of CodeUnits."""
        # First pass: register all known function/method names → qualified id
        name_to_id: dict[str, list[str]] = {}
        for u in units:
            if u.unit_type in (CodeUnitType.FUNCTION, CodeUnitType.METHOD):
                node_id = f"{u.file_path}::{u.name}"
                self.graph.add_node(node_id, **{
                    "name": u.name,
                    "file_path": u.file_path,
                    "unit_type": u.unit_type.value,
                    "start_line": u.start_line,
                })
                name_to_id.setdefault(u.name, []).append(node_id)

        # Second pass: add call edges
        for u in units:
            if u.unit_type not in (CodeUnitType.FUNCTION, CodeUnitType.METHOD):
                continue
            caller_id = f"{u.file_path}::{u.name}"
            for callee_name in u.calls:
                for callee_id in name_to_id.get(callee_name, []):
                    if callee_id != caller_id:
                        self.graph.add_edge(caller_id, callee_id)

        return self

    # ── Query ──────────────────────────────────────────────────────────── #
    def callers_of(self, func_name: str) -> list[str]:
        """Return node IDs that call *func_name*."""
        matches = [n for n in self.graph.nodes if n.endswith(f"::{func_name}")]
        result: list[str] = []
        for m in matches:
            result.extend(list(self.graph.predecessors(m)))
        return result

    def callees_of(self, func_name: str) -> list[str]:
        """Return node IDs that *func_name* calls."""
        matches = [n for n in self.graph.nodes if n.endswith(f"::{func_name}")]
        result: list[str] = []
        for m in matches:
            result.extend(list(self.graph.successors(m)))
        return result

    def trace_from(self, func_name: str, max_depth: int = 5) -> list[str]:
        """BFS execution trace starting from *func_name*."""
        starts = [n for n in self.graph.nodes if n.endswith(f"::{func_name}")]
        if not starts:
            return []
        visited: list[str] = []
        queue = [(starts[0], 0)]
        seen: set[str] = set()
        while queue:
            node, depth = queue.pop(0)
            if node in seen or depth > max_depth:
                continue
            seen.add(node)
            visited.append(node)
            for succ in self.graph.successors(node):
                queue.append((succ, depth + 1))
        return visited

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

    def summary_text(self, func_name: str) -> str:
        trace = self.trace_from(func_name)
        if not trace:
            return f"No call chain found starting from `{func_name}`."
        lines = [f"Call chain from `{func_name}`:"]
        for i, node in enumerate(trace):
            indent = "  " * i
            short = node.split("::")[-1]
            file_part = node.split("::")[0]
            lines.append(f"{indent}→ {short}  [{file_part}]")
        return "\n".join(lines)
