"""
app.py — Streamlit UI for the AI Codebase Intelligence Platform.
"""
import json
import streamlit as st
import requests
import plotly.graph_objects as go
import networkx as nx

API_BASE = "http://localhost:8000/api"

# ── Page config ────────────────────────────────────────────────────────────── #
st.set_page_config(
    page_title="AI Codebase Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────── #
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header { color: #94a3b8; font-size: 1rem; margin-bottom: 2rem; }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 1.5rem;
    }
    .source-chip {
        display: inline-block;
        background: #1e293b;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.78rem;
        color: #94a3b8;
        margin: 2px;
        font-family: monospace;
    }
    .stButton>button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────── #
with st.sidebar:
    st.markdown("## 🧠 Codebase Intelligence")
    st.markdown("---")

    st.markdown("### 📥 Ingest Repository")
    repo_url = st.text_input(
        "GitHub URL",
        placeholder="https://github.com/user/repo",
        key="repo_url_input",
    )
    force_reingest = st.checkbox("Force re-index", value=False)

    if st.button("🚀 Ingest Repository", use_container_width=True):
        if not repo_url:
            st.error("Please enter a GitHub URL.")
        else:
            with st.spinner("Cloning, parsing, and indexing..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/ingest-repo",
                        json={"repo_url": repo_url, "force": force_reingest},
                        timeout=300,
                    )
                    if resp.ok:
                        data = resp.json()
                        st.session_state["repo_id"] = data["repo_id"]
                        st.session_state["ingest_data"] = data
                        st.success(f"✅ Indexed! repo_id: `{data['repo_id']}`")
                    else:
                        st.error(f"Error: {resp.json().get('detail', resp.text)}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Is the backend running?")

    st.markdown("---")
    st.markdown("### 🔖 Active Repository")
    repo_id = st.text_input(
        "Repo ID (auto-filled after ingest)",
        value=st.session_state.get("repo_id", ""),
        key="repo_id_manual",
    )
    if repo_id:
        st.session_state["repo_id"] = repo_id

    # Quick status check
    if repo_id and st.button("Check Status", use_container_width=True):
        try:
            r = requests.get(f"{API_BASE}/repo-status/{repo_id}", timeout=10)
            if r.ok:
                s = r.json()
                st.info(f"📦 {s['chunk_count']} chunks | 🔗 {s['node_count']} nodes")
        except Exception:
            st.warning("Could not fetch status.")

    st.markdown("---")
    st.markdown(
        "<small style='color:#64748b'>Built with FastAPI + ChromaDB + Claude</small>",
        unsafe_allow_html=True,
    )


# ── Main area ──────────────────────────────────────────────────────────────── #
st.markdown('<div class="main-header">🧠 AI Codebase Intelligence Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Understand any codebase like a senior engineer who\'s worked on it for years.</div>', unsafe_allow_html=True)

# Show ingest metrics if available
if "ingest_data" in st.session_state:
    d = st.session_state["ingest_data"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📁 Files Scanned", d.get("files_scanned", "-"))
    c2.metric("🔍 Units Parsed", d.get("units_parsed", "-"))
    c3.metric("🧮 Chunks Stored", d.get("units_embedded", "-"))
    c4.metric("⏱ Duration", f"{d.get('duration_seconds', 0):.1f}s")
    st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────── #
tab1, tab2, tab3, tab4 = st.tabs(["💬 Ask Questions", "🔍 Trace Flow", "🏗 Architecture", "🗺 Graph Explorer"])

active_repo_id = st.session_state.get("repo_id", "")


# ── Tab 1: Q&A ─────────────────────────────────────────────────────────────── #
with tab1:
    st.markdown("### 💬 Ask Anything About the Codebase")

    example_questions = [
        "How does the authentication system work?",
        "Where is the database connection implemented?",
        "Explain the payment module.",
        "What does the main entry point do?",
        "Which files handle user registration?",
        "What services does the order service interact with?",
    ]

    col1, col2 = st.columns([3, 1])
    with col2:
        selected_example = st.selectbox("📋 Example questions", ["(custom)"] + example_questions)

    with col1:
        if selected_example != "(custom)":
            question_default = selected_example
        else:
            question_default = st.session_state.get("last_question", "")
        question = st.text_area(
            "Your question",
            value=question_default,
            height=80,
            placeholder="e.g. How does the authentication system work?",
        )

    if st.button("🔍 Ask Question", use_container_width=False):
        if not active_repo_id:
            st.error("No repo loaded. Ingest a repository first.")
        elif not question:
            st.error("Please enter a question.")
        else:
            st.session_state["last_question"] = question
            with st.spinner("Searching codebase and reasoning..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/ask-question",
                        json={"repo_id": active_repo_id, "question": question},
                        timeout=120,
                    )
                    if resp.ok:
                        data = resp.json()
                        st.session_state["last_answer"] = data
                    else:
                        st.error(resp.json().get("detail", resp.text))
                except Exception as e:
                    st.error(f"Request failed: {e}")

    if "last_answer" in st.session_state:
        ans = st.session_state["last_answer"]
        st.markdown("---")
        st.markdown("#### 🤖 Answer")
        st.markdown(ans["answer"])

        if ans.get("source_files"):
            st.markdown("**📁 Source Files Referenced:**")
            chips = " ".join(f'<span class="source-chip">{f}</span>' for f in ans["source_files"])
            st.markdown(chips, unsafe_allow_html=True)

        if ans.get("trace_text"):
            with st.expander("📊 Execution Trace"):
                st.markdown(ans["trace_text"])


# ── Tab 2: Trace Flow ──────────────────────────────────────────────────────── #
with tab2:
    st.markdown("### 🔍 Trace Execution Flow")
    st.markdown("Enter the name of an entry function to trace the full execution path.")

    col1, col2 = st.columns([3, 1])
    with col1:
        entry_func = st.text_input("Entry function name", placeholder="e.g. login, handle_request, main")
    with col2:
        max_depth = st.slider("Max depth", min_value=2, max_value=10, value=6)

    if st.button("🔗 Trace Flow", use_container_width=False):
        if not active_repo_id:
            st.error("No repo loaded.")
        elif not entry_func:
            st.error("Enter a function name.")
        else:
            with st.spinner(f"Tracing `{entry_func}`..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/trace-flow",
                        json={
                            "repo_id": active_repo_id,
                            "entry_function": entry_func,
                            "max_depth": max_depth,
                        },
                        timeout=120,
                    )
                    if resp.ok:
                        st.session_state["trace_result"] = resp.json()
                    else:
                        st.error(resp.json().get("detail", resp.text))
                except Exception as e:
                    st.error(f"Request failed: {e}")

    if "trace_result" in st.session_state:
        tr = st.session_state["trace_result"]
        st.markdown("---")

        if tr.get("trace_text"):
            st.markdown("#### 🗺 Execution Path")
            st.markdown(tr["trace_text"])

        st.markdown("#### 🤖 Explanation")
        st.markdown(tr["answer"])

        if tr.get("source_files"):
            st.markdown("**📁 Files Involved:**")
            chips = " ".join(f'<span class="source-chip">{f}</span>' for f in tr["source_files"])
            st.markdown(chips, unsafe_allow_html=True)


# ── Tab 3: Architecture ────────────────────────────────────────────────────── #
with tab3:
    st.markdown("### 🏗 Architecture Overview")

    if st.button("🏗 Generate Architecture Analysis", use_container_width=False):
        if not active_repo_id:
            st.error("No repo loaded.")
        else:
            with st.spinner("Analysing architecture..."):
                try:
                    resp = requests.get(
                        f"{API_BASE}/get-architecture/{active_repo_id}",
                        timeout=120,
                    )
                    if resp.ok:
                        st.session_state["arch_result"] = resp.json()
                    else:
                        st.error(resp.json().get("detail", resp.text))
                except Exception as e:
                    st.error(f"Request failed: {e}")

    if "arch_result" in st.session_state:
        ar = st.session_state["arch_result"]
        st.markdown("---")
        st.markdown(ar["answer"])


# ── Tab 4: Graph Explorer ──────────────────────────────────────────────────── #
with tab4:
    st.markdown("### 🗺 Interactive Graph Explorer")

    graph_type = st.radio("Graph Type", ["Dependency Graph", "Call Graph"], horizontal=True)

    def render_graph(graph_data: dict, title: str):
        if not graph_data or not graph_data.get("nodes"):
            st.info("No graph data available.")
            return

        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        # Build NetworkX layout
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node["id"])
        for edge in edges:
            G.add_edge(edge["source"], edge["target"])

        if len(G.nodes) == 0:
            st.info("Graph is empty.")
            return

        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        # Build Plotly figure
        edge_x, edge_y = [], []
        for e in G.edges():
            x0, y0 = pos[e[0]]
            x1, y1 = pos[e[1]]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        node_x = [pos[n][0] for n in G.nodes()]
        node_y = [pos[n][1] for n in G.nodes()]
        node_labels = [n.split("::")[-1] if "::" in n else n.split("/")[-1] for n in G.nodes()]
        node_text = list(G.nodes())

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode="lines",
            line=dict(width=0.8, color="#475569"),
            hoverinfo="none",
        ))
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            text=node_labels,
            textposition="top center",
            textfont=dict(size=9, color="#e2e8f0"),
            hovertext=node_text,
            hoverinfo="text",
            marker=dict(
                size=10,
                color="#6366f1",
                line=dict(width=1, color="#818cf8"),
            ),
        ))
        fig.update_layout(
            title=title,
            showlegend=False,
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font=dict(color="#e2e8f0"),
            margin=dict(l=20, r=20, t=40, b=20),
            height=600,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    if st.button("📊 Load Graph", use_container_width=False):
        if not active_repo_id:
            st.error("No repo loaded.")
        else:
            with st.spinner("Fetching graph data..."):
                try:
                    # Get architecture data which includes dep graph
                    resp = requests.get(f"{API_BASE}/get-architecture/{active_repo_id}", timeout=60)
                    if resp.ok:
                        st.session_state["graph_arch"] = resp.json()
                    # Also ask a generic question to get call graph
                    resp2 = requests.post(
                        f"{API_BASE}/ask-question",
                        json={"repo_id": active_repo_id, "question": "What are the main functions?"},
                        timeout=120,
                    )
                    if resp2.ok:
                        st.session_state["graph_qa"] = resp2.json()
                except Exception as e:
                    st.error(f"Failed: {e}")

    if graph_type == "Dependency Graph" and "graph_arch" in st.session_state:
        render_graph(
            st.session_state["graph_arch"].get("dependency_graph"),
            "Module Dependency Graph"
        )
    elif graph_type == "Call Graph" and "graph_qa" in st.session_state:
        render_graph(
            st.session_state["graph_qa"].get("call_graph"),
            "Function Call Graph"
        )
    else:
        st.info("Click 'Load Graph' after ingesting a repository.")

    # Also list functions
    if active_repo_id and st.button("📋 List All Functions"):
        try:
            r = requests.get(f"{API_BASE}/list-functions/{active_repo_id}?limit=100", timeout=30)
            if r.ok:
                data = r.json()
                st.markdown(f"**{data['total']} functions found** (showing {len(data['functions'])})")
                func_data = [
                    {"Function": f["name"], "File": f["file"], "Type": f["type"]}
                    for f in data["functions"]
                ]
                st.dataframe(func_data, use_container_width=True)
        except Exception as e:
            st.error(f"Failed: {e}")
