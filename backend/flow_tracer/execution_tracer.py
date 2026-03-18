"""
execution_tracer.py — Trace an execution flow through the call graph,
enriched with code snippets and a natural-language narrative.
"""
from __future__ import annotations
from dataclasses import dataclass

from backend.graphs.call_graph import CallGraph
from backend.parsing.code_unit import CodeUnit


@dataclass
class TraceStep:
    func_name: str
    file_path: str
    code_snippet: str
    depth: int


@dataclass
class ExecutionTrace:
    entry_point: str
    steps: list[TraceStep]

    def to_text(self) -> str:
        lines = [f"## Execution Trace: `{self.entry_point}`\n"]
        for step in self.steps:
            indent = "  " * step.depth
            lines.append(f"{indent}{'→ ' if step.depth else ''}**{step.func_name}**  `{step.file_path}`")
            if step.code_snippet:
                preview = step.code_snippet[:200].replace("\n", " ").strip()
                lines.append(f"{indent}  _{preview}..._")
        return "\n".join(lines)


class ExecutionTracer:
    def __init__(self, call_graph: CallGraph, units: list[CodeUnit]):
        self.call_graph = call_graph
        # Build quick lookup: (file_path, name) → code snippet
        self._code_map: dict[str, str] = {}
        for u in units:
            key = f"{u.file_path}::{u.name}"
            self._code_map[key] = u.code[:300]

    def trace(self, entry_func: str, max_depth: int = 6) -> ExecutionTrace:
        """Trace execution starting from *entry_func*."""
        node_ids = self.call_graph.trace_from(entry_func, max_depth=max_depth)

        steps: list[TraceStep] = []
        for i, node_id in enumerate(node_ids):
            parts = node_id.split("::")
            file_path = parts[0]
            func_name = parts[-1]
            snippet = self._code_map.get(node_id, "")

            # Compute depth by checking if node was discovered through BFS layers
            depth = self._compute_depth(node_id, node_ids[:i])
            steps.append(TraceStep(
                func_name=func_name,
                file_path=file_path,
                code_snippet=snippet,
                depth=min(depth, max_depth),
            ))

        return ExecutionTrace(entry_point=entry_func, steps=steps)

    def _compute_depth(self, node: str, previous: list[str]) -> int:
        """Approximate depth by checking predecessors in previously seen nodes."""
        preds = set(self.call_graph.graph.predecessors(node))
        for i, prev in enumerate(reversed(previous)):
            if prev in preds:
                return len(previous) - i
        return 0
