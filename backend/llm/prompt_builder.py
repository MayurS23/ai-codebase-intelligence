"""
prompt_builder.py — Construct structured prompts for each query type.
"""
from __future__ import annotations

SYSTEM_BASE = """You are an expert AI software engineer with deep knowledge of \
large-scale codebases. You have been given context from a real GitHub repository \
and must answer the developer's question accurately and concisely.

Rules:
- Base your answer ONLY on the provided code context.
- Reference specific file paths and function names when relevant.
- If you're unsure, say so — do not hallucinate.
- Format your answer in clean Markdown.
- Be precise and developer-friendly.
"""


def build_qa_prompt(context: str, question: str, call_graph_text: str = "") -> tuple[str, str]:
    """Returns (system_prompt, user_message) for a general code Q&A."""
    system = SYSTEM_BASE

    extra = ""
    if call_graph_text:
        extra = f"\n\n## Call Graph Context\n{call_graph_text}"

    user = f"""## Code Context from Repository
{context}
{extra}

## Developer Question
{question}

Please provide a thorough, accurate answer based on the code above."""
    return system, user


def build_trace_prompt(context: str, trace_text: str, question: str) -> tuple[str, str]:
    """Returns prompts for an execution flow trace question."""
    system = SYSTEM_BASE + "\nFor flow traces, present steps in order, with file locations."

    user = f"""## Code Context
{context}

## Execution Trace
{trace_text}

## Question
{question}

Explain the execution flow in detail, describing what each step does."""
    return system, user


def build_architecture_prompt(
    file_tree: str,
    dep_graph_summary: str,
    most_imported: list[tuple[str, int]],
) -> tuple[str, str]:
    """Returns prompts for an architecture summary."""
    system = SYSTEM_BASE + "\nFocus on high-level architecture, module responsibilities, and data flow."

    imported_lines = "\n".join(f"  - {f} (imported by {n} files)" for f, n in most_imported)

    user = f"""## Repository File Tree
{file_tree}

## Module Dependency Summary
{dep_graph_summary}

## Most Central Files (by import count)
{imported_lines}

Generate a comprehensive architecture overview:
1. What kind of application/system is this?
2. What are the main modules and their responsibilities?
3. How do modules interact?
4. What are the entry points?
5. What patterns (MVC, microservices, etc.) are used?"""
    return system, user
