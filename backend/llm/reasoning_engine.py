"""
reasoning_engine.py — Orchestrates retrieval + graph enrichment + LLM.
FIX: handle None entry_func in trace, guard against empty retrieval
"""
from __future__ import annotations
from dataclasses import dataclass, field

from backend.retrieval.retrieval_engine import RetrievalEngine
from backend.graphs.call_graph import CallGraph
from backend.graphs.dependency_graph import DependencyGraph
from backend.flow_tracer.execution_tracer import ExecutionTracer
from backend.llm.llm_client import LLMClient
from backend.llm.prompt_builder import (
    build_qa_prompt,
    build_trace_prompt,
    build_architecture_prompt,
)
from backend.parsing.code_unit import CodeUnit


@dataclass
class AnswerResponse:
    answer: str
    source_files: list[str] = field(default_factory=list)
    call_graph_data: dict | None = None
    dependency_graph_data: dict | None = None
    trace_text: str | None = None


TRACE_KEYWORDS = {"trace", "flow", "path", "execution", "walk", "follow", "journey", "step"}
ARCH_KEYWORDS  = {"architecture", "overview", "structure", "modules", "system", "design", "layout"}


class ReasoningEngine:
    def __init__(
        self,
        repo_id: str,
        units: list[CodeUnit],
        call_graph: CallGraph,
        dep_graph: DependencyGraph,
    ):
        self.repo_id    = repo_id
        self.units      = units
        self.call_graph = call_graph
        self.dep_graph  = dep_graph
        self.retrieval  = RetrievalEngine(repo_id)
        self.llm        = LLMClient()
        self.tracer     = ExecutionTracer(call_graph, units)

    def answer(self, question: str) -> AnswerResponse:
        q_lower = question.lower()
        if any(kw in q_lower for kw in ARCH_KEYWORDS):
            return self._answer_architecture(question)
        if any(kw in q_lower for kw in TRACE_KEYWORDS):
            return self._answer_trace(question)
        return self._answer_qa(question)

    # ── General Q&A ──────────────────────────────────────────────────────── #
    def _answer_qa(self, question: str) -> AnswerResponse:
        ctx = self.retrieval.retrieve(question, top_k=12)
        prompt_ctx = ctx.to_prompt_context()

        cg_text = ""
        if ctx.results:
            top_func = ctx.results[0].metadata.get("name", "")
            if top_func:
                cg_text = self.call_graph.summary_text(top_func)

        system, user = build_qa_prompt(prompt_ctx, question, cg_text)
        answer = self.llm.complete(system, user)

        return AnswerResponse(
            answer=answer,
            source_files=ctx.source_files(),
            call_graph_data=self.call_graph.to_dict(),
            dependency_graph_data=self.dep_graph.to_dict(),
        )

    # ── Execution flow trace ──────────────────────────────────────────────── #
    def _answer_trace(self, question: str) -> AnswerResponse:
        entry_func = self._extract_func_name(question) or self._infer_entry(question)

        trace_text = ""
        if entry_func:
            trace = self.tracer.trace(entry_func, max_depth=6)
            trace_text = trace.to_text()
        else:
            trace_text = "Could not identify an entry function from the question."

        ctx = self.retrieval.retrieve(question, top_k=8)
        system, user = build_trace_prompt(ctx.to_prompt_context(), trace_text, question)
        answer = self.llm.complete(system, user)

        return AnswerResponse(
            answer=answer,
            source_files=ctx.source_files(),
            trace_text=trace_text,
            call_graph_data=self.call_graph.to_dict(),
        )

    # ── Architecture overview ─────────────────────────────────────────────── #
    def _answer_architecture(self, question: str) -> AnswerResponse:
        files = sorted(set(u.file_path for u in self.units))
        file_tree = self._build_tree_string(files)

        clusters = self.dep_graph.cluster_by_directory()
        dep_lines = [f"  {d}/: {len(fs)} files" for d, fs in clusters.items()]
        dep_summary = "\n".join(dep_lines) or "  (no dependency data)"

        most_imported = self.dep_graph.most_imported(top_n=8)

        system, user = build_architecture_prompt(file_tree, dep_summary, most_imported)
        answer = self.llm.complete(system, user)

        return AnswerResponse(
            answer=answer,
            source_files=files[:20],
            dependency_graph_data=self.dep_graph.to_dict(),
        )

    # ── Helpers ───────────────────────────────────────────────────────────── #
    def _extract_func_name(self, question: str) -> str | None:
        import re
        m = re.search(r"[`'\"](\w+)[`'\"]|\b(\w+)\(\)", question)
        if m:
            return m.group(1) or m.group(2)
        return None

    def _infer_entry(self, question: str) -> str | None:
        ctx = self.retrieval.retrieve(question, top_k=3)
        if ctx.results:
            name = ctx.results[0].metadata.get("name", "")
            return name if name else None
        return None

    def _build_tree_string(self, files: list[str], max_files: int = 80) -> str:
        shown = files[:max_files]
        lines = [f"  {f}" for f in shown]
        if len(files) > max_files:
            lines.append(f"  ... and {len(files) - max_files} more files")
        return "\n".join(lines)
