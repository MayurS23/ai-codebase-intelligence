"""
test_graphs.py — Unit tests for call graph and dependency graph builders.
"""
from backend.parsing.python_parser import parse_python_file
from backend.graphs.call_graph import CallGraph
from backend.graphs.dependency_graph import DependencyGraph

CODE = '''
import auth_service

def login(username, password):
    user = authenticate_user(username, password)
    token = generate_token(user)
    return token

def authenticate_user(username, password):
    return {"username": username}

def generate_token(user):
    return user["username"] + "_tok"
'''


def _get_units():
    return parse_python_file("repo", "app.py", CODE)


def test_call_graph_nodes():
    units = _get_units()
    cg = CallGraph(repo_id="repo").build(units)
    node_names = [cg.graph.nodes[n].get("name") for n in cg.graph.nodes]
    assert "login" in node_names
    assert "authenticate_user" in node_names


def test_call_graph_edges():
    units = _get_units()
    cg = CallGraph(repo_id="repo").build(units)
    edges = [(u.split("::")[-1], v.split("::")[-1]) for u, v in cg.graph.edges]
    assert ("login", "authenticate_user") in edges or ("login", "generate_token") in edges


def test_trace_from():
    units = _get_units()
    cg = CallGraph(repo_id="repo").build(units)
    trace = cg.trace_from("login", max_depth=3)
    # login should be in trace
    assert any("login" in t for t in trace)


def test_dep_graph_module_nodes():
    units = _get_units()
    dg = DependencyGraph(repo_id="repo").build(units)
    assert dg.graph.number_of_nodes() >= 1


def test_summary_text():
    units = _get_units()
    cg = CallGraph(repo_id="repo").build(units)
    text = cg.summary_text("login")
    assert "login" in text
