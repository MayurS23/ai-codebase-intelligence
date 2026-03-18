# 🧠 AI Codebase Intelligence Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=for-the-badge&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36-red?style=for-the-badge&logo=streamlit)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-purple?style=for-the-badge)
![Claude AI](https://img.shields.io/badge/Claude-Anthropic-orange?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-50%20Passing-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**An AI-powered system that ingests any GitHub repository and lets you talk to it like a senior engineer who has worked on it for years.**

[Features](#-features) • [Demo](#-how-it-works) • [Installation](#-installation) • [Usage](#-usage) • [API Docs](#-api-reference) • [Architecture](#-architecture)

</div>

---

## 📌 What Is This?

The **AI Codebase Intelligence Platform** is a developer tool that combines **Retrieval Augmented Generation (RAG)**, **static code analysis**, **call graph generation**, and **LLM reasoning** to help developers understand large, complex codebases instantly.

Instead of spending hours reading through thousands of files, you simply paste a GitHub URL and ask questions in plain English:

- *"How does the authentication system work?"*
- *"Trace the login execution flow"*
- *"Which files are involved when a user signs up?"*
- *"Explain the payment module"*
- *"What services interact with the order service?"*

The system answers like a senior engineer who has deeply studied the codebase.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Codebase Q&A** | Ask any natural language question about any GitHub repo |
| 🔗 **Execution Flow Tracing** | Trace how execution flows from any entry function |
| 🏗 **Architecture Analysis** | Get a high-level overview of the entire system design |
| 📊 **Call Graph Builder** | Visualize which functions call which other functions |
| 🗺 **Dependency Graph** | See how files and modules depend on each other |
| 🌐 **Multi-Language Support** | Python, JavaScript, TypeScript, Java, Go, Rust, C++, C#, Ruby, PHP, Kotlin, Swift |
| 💾 **Persistent Indexing** | Index once, query forever — no re-processing needed |
| ⚡ **Semantic Search** | Finds relevant code even when exact keywords don't match |
| 🔄 **Session Recovery** | Restore your session after server restart without re-embedding |
| 🐳 **Docker Support** | One command to run everything |

---

## 🖥 How It Works

```
You paste a GitHub URL
        │
        ▼
┌─────────────────────────────────────────────────────┐
│                  INGESTION PIPELINE                  │
│                                                      │
│  Clone Repo → Scan Files → Parse AST → Chunk Code  │
│       → Generate Embeddings → Store in ChromaDB     │
│       → Build Call Graph → Build Dependency Graph   │
└─────────────────────────────────────────────────────┘
        │
        ▼
You ask a question
        │
        ▼
┌─────────────────────────────────────────────────────┐
│                   QUERY PIPELINE                     │
│                                                      │
│  Embed Question → Search ChromaDB → Retrieve Top-K  │
│    Chunks → Enrich with Graph Data → Build Prompt   │
│             → Send to Claude AI → Get Answer        │
└─────────────────────────────────────────────────────┘
        │
        ▼
You get a precise, developer-quality answer with source file references
```

---

## 🧰 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | Anthropic Claude (claude-sonnet-4) | Code reasoning & explanation |
| **Embeddings** | OpenAI text-embedding-3-small | Semantic code search |
| **Vector Database** | ChromaDB | Store & retrieve code embeddings |
| **Parsing** | Python AST + Regex | Extract functions, classes, imports |
| **Graph Engine** | NetworkX | Call graphs & dependency graphs |
| **Backend API** | FastAPI + Uvicorn | REST API endpoints |
| **Frontend** | Streamlit + Plotly | Interactive UI & graph visualization |
| **Version Control** | Git | Source control |
| **Containerization** | Docker + Docker Compose | Deployment |

---

## 📁 Project Structure

```
ai-codebase-intelligence/
│
├── 📂 backend/                        # FastAPI backend
│   ├── main.py                        # App entry point
│   ├── config.py                      # All configuration via .env
│   │
│   ├── 📂 ingestion/
│   │   ├── repo_cloner.py             # Clone GitHub repos
│   │   ├── file_scanner.py            # Walk dirs, detect code files
│   │   └── ingestion_orchestrator.py  # Full pipeline coordinator
│   │
│   ├── 📂 parsing/
│   │   ├── code_unit.py               # Core data model (CodeUnit)
│   │   ├── python_parser.py           # Python AST parser
│   │   ├── generic_parser.py          # Regex parser for other languages
│   │   └── parser_dispatcher.py       # Routes files to correct parser
│   │
│   ├── 📂 chunking/
│   │   └── smart_chunker.py           # Function/class-level chunking
│   │
│   ├── 📂 embeddings/
│   │   ├── embedding_model.py         # OpenAI + local fallback model
│   │   └── embedding_pipeline.py      # Batch embedding processor
│   │
│   ├── 📂 vectordb/
│   │   └── chroma_store.py            # ChromaDB store & search
│   │
│   ├── 📂 retrieval/
│   │   └── retrieval_engine.py        # Semantic search + re-ranking
│   │
│   ├── 📂 graphs/
│   │   ├── call_graph.py              # Function call relationships
│   │   └── dependency_graph.py        # File/module dependencies
│   │
│   ├── 📂 flow_tracer/
│   │   └── execution_tracer.py        # BFS execution path tracer
│   │
│   ├── 📂 llm/
│   │   ├── llm_client.py              # Claude API wrapper
│   │   ├── prompt_builder.py          # Structured prompt templates
│   │   └── reasoning_engine.py        # Orchestrates RAG + LLM
│   │
│   └── 📂 api/
│       ├── session_cache.py           # In-memory session store
│       ├── 📂 routes/
│       │   ├── ingest.py              # POST /ingest-repo
│       │   ├── query.py               # POST /ask-question, /trace-flow
│       │   └── architecture.py        # GET /get-architecture, /repo-status
│       └── 📂 models/
│           └── schemas.py             # Pydantic request/response models
│
├── 📂 frontend/
│   └── app.py                         # Streamlit UI (4 tabs)
│
├── 📂 tests/                          # 50 tests — all passing
│   ├── conftest.py                    # Shared fixtures
│   ├── test_api.py                    # FastAPI endpoint tests
│   ├── test_parsing.py                # Parser tests
│   ├── test_graphs.py                 # Graph builder tests
│   ├── test_embeddings.py             # Embedding model tests
│   ├── test_vectordb.py               # ChromaDB tests
│   ├── test_retrieval.py              # Retrieval engine tests
│   ├── test_ingestion.py              # Full pipeline integration tests
│   └── test_flow_tracer.py            # Execution tracer tests
│
├── 📂 docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── 📂 .vscode/                        # VS Code launch configs
│   ├── settings.json
│   ├── launch.json                    # One-click run backend/frontend/tests
│   └── extensions.json                # Recommended extensions
│
├── api.http                           # VS Code REST Client test file
├── setup.bat                          # Windows one-click setup
├── start_backend.bat                  # Start FastAPI server
├── start_frontend.bat                 # Start Streamlit UI
├── run_tests.bat                      # Run all 50 tests
├── requirements.txt                   # All Python dependencies
├── pyproject.toml                     # Project metadata + pytest config
└── .env.example                       # Environment variable template
```

---

## ⚙️ Prerequisites

Before you begin, make sure you have the following installed:

| Requirement | Version | Download |
|---|---|---|
| **Python** | 3.10 or higher | [python.org](https://www.python.org/downloads/) |
| **Git** | Any recent version | [git-scm.com](https://git-scm.com/downloads) |
| **VS Code** | Latest | [code.visualstudio.com](https://code.visualstudio.com/) |

### Check if Python and Git are installed:

Open Command Prompt (`Win + R` → type `cmd` → Enter) and run:

```cmd
python --version
git --version
```

You should see version numbers. If not, install them from the links above.

---

## 🔑 API Keys Required

You need **at least one** of the following:

### Option A — Full Quality (Recommended)
| Key | Where to Get | Cost |
|---|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Free trial available |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | Free $5 credits on signup |

### Option B — No API Keys (Offline Mode)
Set `EMBEDDING_PROVIDER=local` in your `.env` file. The system will use a built-in TF-IDF embedding model. Quality will be lower but it works 100% offline. You still need an Anthropic key for LLM answers though.

---

## 🚀 Installation

### Step 1 — Clone the Repository

```cmd
git clone https://github.com/MayurS23/ai-codebase-intelligence.git
cd ai-codebase-intelligence
```

### Step 2 — Run the Setup Script (Windows)

```cmd
setup.bat
```

This will automatically:
- ✅ Create a Python virtual environment (`.venv`)
- ✅ Install all dependencies from `requirements.txt`
- ✅ Create your `.env` file from the template
- ✅ Create required data directories

### Step 3 — Configure Your API Keys

Open the `.env` file in VS Code and fill in your keys:

```env
# ── LLM (Required for answering questions) ──────────────
ANTHROPIC_API_KEY=sk-ant-your-key-here

# ── Embeddings (Required for semantic search) ────────────
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# ── Or use local embeddings (no OpenAI key needed) ───────
# EMBEDDING_PROVIDER=local

# ── These defaults work fine, no need to change ──────────
LLM_MODEL=claude-sonnet-4-20250514
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./data/chromadb
REPOS_DIR=./data/repos
MAX_FILE_SIZE_KB=500
API_HOST=0.0.0.0
API_PORT=8000
```

Save the file with **Ctrl+S**.

### Step 4 — Verify Installation (Run Tests)

```cmd
run_tests.bat
```

You should see:
```
50 passed in ~11s
```

If all 50 tests pass, your installation is complete. ✅

---

## ▶️ Running the Application

You need **two terminals** open at the same time.

### Terminal 1 — Start the Backend API

```cmd
start_backend.bat
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Visit `http://localhost:8000/docs` to see the interactive API documentation.

### Terminal 2 — Start the Frontend UI

```cmd
start_frontend.bat
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Open the App

Go to **`http://localhost:8501`** in your browser. 🎉

---

## 💻 Using the Application

### 1. Ingest a Repository

In the sidebar on the left:
1. Paste any GitHub URL, for example:
   ```
   https://github.com/pallets/flask
   ```
2. Click **🚀 Ingest Repository**
3. Wait for processing (1–5 minutes depending on repo size)
4. You'll see metrics: files scanned, units parsed, chunks stored

### 2. Ask Questions (Tab 1 — 💬 Ask Questions)

Type any question about the codebase:

```
How does routing work?
Where is the database connection handled?
What does the application factory do?
Which files are involved in request handling?
Explain the templating system
```

The system will return:
- A detailed answer with code references
- The source files it used to generate the answer
- Call graph context

### 3. Trace Execution Flow (Tab 2 — 🔍 Trace Flow)

Enter a function name like `full_dispatch_request` and click **Trace Flow**.

You'll see the complete execution path:
```
→ full_dispatch_request  [app.py]
  → dispatch_request  [app.py]
    → ensure_sync  [app.py]
      → view_function  [views.py]
```

### 4. Architecture Overview (Tab 3 — 🏗 Architecture)

Click **Generate Architecture Analysis** to get a full system overview including:
- What kind of application it is
- Main modules and their responsibilities
- How modules interact
- Entry points
- Design patterns used

### 5. Graph Explorer (Tab 4 — 🗺 Graph Explorer)

Visualize the codebase as an interactive graph:
- **Dependency Graph** — which files import which files
- **Call Graph** — which functions call which functions

---

## 🌐 API Reference

The full interactive API docs are available at `http://localhost:8000/docs` when the backend is running.

### Endpoints

#### `POST /api/ingest-repo`
Ingest a GitHub repository.

```json
Request:
{
  "repo_url": "https://github.com/pallets/flask",
  "force": false
}

Response:
{
  "repo_id": "pallets__flask",
  "files_scanned": 45,
  "units_parsed": 312,
  "units_embedded": 389,
  "duration_seconds": 42.3,
  "message": "Repository indexed successfully."
}
```

#### `POST /api/ask-question`
Ask a natural language question.

```json
Request:
{
  "repo_id": "pallets__flask",
  "question": "How does routing work?"
}

Response:
{
  "answer": "Flask routing works through...",
  "source_files": ["src/flask/routing.py", "src/flask/app.py"],
  "call_graph": { "nodes": [...], "edges": [...] }
}
```

#### `POST /api/trace-flow`
Trace execution from an entry function.

```json
Request:
{
  "repo_id": "pallets__flask",
  "entry_function": "full_dispatch_request",
  "max_depth": 5
}
```

#### `GET /api/get-architecture/{repo_id}`
Get architecture overview.

#### `GET /api/repo-status/{repo_id}`
Check if a repo is indexed and session is loaded.

#### `POST /api/reload-session/{repo_id}`
Restore session after server restart (no re-embedding needed).

#### `GET /api/list-functions/{repo_id}`
List all known functions in the indexed repo.

---

## 🐳 Running with Docker

If you have Docker installed, you can run the entire application with one command:

```cmd
cd docker
docker-compose up --build
```

This starts:
- Backend API at `http://localhost:8000`
- Frontend UI at `http://localhost:8501`

To stop:
```cmd
docker-compose down
```

---

## 🧪 Running Tests

```cmd
run_tests.bat
```

Or manually:
```cmd
.venv\Scripts\activate
set PYTHONPATH=%CD%
set EMBEDDING_PROVIDER=local
python -m pytest tests/ -v
```

### Test Coverage

| Test File | What It Tests | Tests |
|---|---|---|
| `test_parsing.py` | Python AST parser, chunker | 8 |
| `test_graphs.py` | Call graph, dependency graph | 5 |
| `test_embeddings.py` | Embedding models, batch pipeline | 5 |
| `test_vectordb.py` | ChromaDB store, search, empty handling | 6 |
| `test_retrieval.py` | Semantic search, re-ranking | 4 |
| `test_flow_tracer.py` | Execution tracing, depth limits | 5 |
| `test_ingestion.py` | File scanner, full pipeline integration | 5 |
| `test_api.py` | All 7 FastAPI endpoints | 12 |
| **Total** | | **50 ✅** |

---

## 🔧 VS Code Integration

This project includes full VS Code configuration.

### One-Click Run (Press F5)

Open the **Run and Debug** panel (`Ctrl+Shift+D`) and select:
- **▶ Run FastAPI Backend** — starts the API server with debugger
- **▶ Run Streamlit Frontend** — starts the UI
- **🧪 Run All Tests** — runs all 50 tests

### Recommended Extensions

When you open the project in VS Code, it will suggest installing:
- **Python** — Python language support
- **Pylance** — Fast Python type checking
- **REST Client** — Test API endpoints from `api.http` file
- **GitLens** — Enhanced Git capabilities

### Test API from VS Code

Open `api.http` in VS Code and click **Send Request** above any endpoint to test it directly.

---

## ❓ Troubleshooting

### `ModuleNotFoundError`
```cmd
.venv\Scripts\activate
pip install -r requirements.txt
```

### `Connection refused on port 8000`
The backend isn't running. Run `start_backend.bat` in a separate terminal.

### `Repo not found` error when asking questions
You need to ingest the repo first via the UI or `POST /api/ingest-repo`.

### `API key invalid`
Double-check your `.env` file. Make sure there are no spaces around the `=` sign:
```
ANTHROPIC_API_KEY=sk-ant-...   ✅ correct
ANTHROPIC_API_KEY = sk-ant-... ❌ wrong
```

### Server restarted and questions stopped working
Run this to restore your session without re-indexing:
```
POST /api/reload-session/{your_repo_id}
```
Or just ingest the repo again (embeddings are cached).

### Tests failing
Make sure you're running tests with local embeddings:
```cmd
set EMBEDDING_PROVIDER=local
python -m pytest tests/ -v
```

---

## 🗺 Architecture Deep Dive

```
┌──────────────────────────────────────────────────────────────────┐
│                         LAYER 1: INGESTION                        │
│   GitHub URL → Clone → Scan Files → Parse AST → CodeUnit objects │
└──────────────────────────────────────┬───────────────────────────┘
                                        │
              ┌─────────────────────────┼────────────────────────┐
              │                         │                          │
              ▼                         ▼                          ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌───────────────────┐
│   LAYER 2: CHUNKS   │   │  LAYER 2: CALL GRAPH │   │ LAYER 2: DEP GRAPH│
│  Split by function/ │   │  function → function │   │  file → file       │
│  class boundaries   │   │  (NetworkX DiGraph)  │   │  (NetworkX DiGraph)│
└──────────┬──────────┘   └─────────────────────┘   └───────────────────┘
           │
           ▼
┌─────────────────────┐
│  LAYER 3: EMBEDDINGS│
│  OpenAI / Local     │
│  text-embedding-3   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   LAYER 4: STORAGE  │
│   ChromaDB          │
│   (vectors +        │
│    metadata)        │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     LAYER 5: INTELLIGENCE                         │
│   Query → Embed → Search ChromaDB → Enrich with Graphs →         │
│   Build Prompt → Claude AI → Answer with source references       │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      LAYER 6: API (FastAPI)                       │
│   /ingest-repo  /ask-question  /trace-flow  /get-architecture    │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 7: UI (Streamlit)                        │
│   Ask Questions │ Trace Flow │ Architecture │ Graph Explorer      │
└──────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

**Why function/class level chunking?**
Most RAG tutorials split code by token count (e.g. 512 tokens). This breaks functions in half, destroying semantic meaning. We chunk at function and class boundaries so the LLM always sees complete, meaningful units of code.

**Why two indexes (vector + graph)?**
Vector search answers "what is this about?" but can't answer "how does A connect to B?" Graph indexes answer structural questions. Combining both gives dramatically better answers than either alone.

**Why metadata-rich chunks?**
Every chunk stored in ChromaDB carries: file path, function name, start/end line number, language, parent class, docstring, and called functions. This enables precise attribution — the LLM can say "this is in `auth.py` line 42" rather than giving vague answers.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `run_tests.bat`
5. Commit: `git commit -m "feat: add my feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Mayur S**
GitHub: [@MayurS23](https://github.com/MayurS23)

---

<div align="center">

**If this project helped you, please give it a ⭐ on GitHub!**

Built with ❤️ using Python, FastAPI, Claude AI, and ChromaDB

</div>