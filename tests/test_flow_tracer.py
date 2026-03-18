"""test_flow_tracer.py — ExecutionTracer tests."""
from backend.flow_tracer.execution_tracer import ExecutionTracer


def test_trace_returns_steps(call_graph, parsed_units):
    tracer = ExecutionTracer(call_graph, parsed_units)
    trace  = tracer.trace("login", max_depth=4)
    assert len(trace.steps) > 0


def test_trace_entry_point(call_graph, parsed_units):
    tracer = ExecutionTracer(call_graph, parsed_units)
    trace  = tracer.trace("login")
    assert trace.entry_point == "login"


def test_trace_to_text(call_graph, parsed_units):
    tracer = ExecutionTracer(call_graph, parsed_units)
    trace  = tracer.trace("login")
    text   = trace.to_text()
    assert "login" in text
    assert "##" in text          # Markdown heading


def test_trace_unknown_function(call_graph, parsed_units):
    """Tracing a non-existent function should return empty steps gracefully."""
    tracer = ExecutionTracer(call_graph, parsed_units)
    trace  = tracer.trace("nonexistent_xyz_func")
    assert isinstance(trace.steps, list)


def test_trace_depth_respected(call_graph, parsed_units):
    tracer = ExecutionTracer(call_graph, parsed_units)
    trace  = tracer.trace("login", max_depth=1)
    # All steps should have depth <= 1
    assert all(s.depth <= 1 for s in trace.steps)
