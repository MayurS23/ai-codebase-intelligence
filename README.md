# 🧠 AI Codebase Intelligence Platform

> Understand any GitHub repository like a senior engineer who's worked on it for years.

## What It Does

- **Ingest** any GitHub repository — clone, parse, embed, index
- **Answer questions** about the codebase in natural language
- **Trace execution flows** through call graphs
- **Generate architecture overviews** of entire systems
- **Visualize** dependency graphs and call graphs interactively

## Quick Start

### 1. Clone & Setup

```bash
git clone <this-repo>
cd ai-codebase-intelligence
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Backend API

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the Frontend

```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501` in your browser.

---

## Usage

### Via UI

1. Paste a GitHub repo URL in the sidebar
2. Click **Ingest Repository**
3. Ask questions in the **Ask Questions** tab
4. Trace flows in the **Trace Flow** tab
5. View the **Architecture** and **Graph Explorer** tabs

### Via API

**Ingest a repository:**
```bash
curl -X POST http://localhost:8000/api/ingest-repo \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/pallets/flask"}'
```

**Ask a question:**
```bash
curl -X POST http://localhost:8000/api/ask-question \
  -H "Content-Type: application/json" \
  -d '{"repo_id": "pallets__flask", "question": "How does routing work?"}'
```

**Trace execution flow:**
```bash
curl -X POST http://localhost:8000/api/trace-flow \
  -H "Content-Type: application/json" \
  -d '{"repo_id": "pallets__flask", "entry_function": "full_dispatch_request"}'
```

**Get architecture overview:**
```bash
curl http://localhost:8000/api/get-architecture/pallets__flask
```

---

## Configuration (.env)

| Variable | Description | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API key | required |
| `OPENAI_API_KEY` | OpenAI embeddings key | required if using OpenAI |
| `EMBEDDING_PROVIDER` | `openai` or `local` | `openai` |
| `LLM_MODEL` | Claude model ID | `claude-sonnet-4-20250514` |
| `CHROMA_PERSIST_DIR` | ChromaDB data dir | `./data/chromadb` |
| `REPOS_DIR` | Cloned repos dir | `./data/repos` |
| `MAX_FILE_SIZE_KB` | Skip files larger than this | `500` |

> **Tip:** Set `EMBEDDING_PROVIDER=local` to run without any API keys (lower quality embeddings).

---

## Architecture

```
GitHub URL
    │
    ▼
Ingestion (clone → scan → parse → chunk → embed → store)
    │                              │
    ▼                              ▼
ChromaDB                     Call Graph + Dependency Graph
(vector index)               (NetworkX DiGraph)
    │                              │
    └──────────────┬───────────────┘
                   ▼
           Reasoning Engine
         (retrieval + LLM + graphs)
                   │
                   ▼
              FastAPI REST
                   │
                   ▼
           Streamlit UI
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| LLM | Anthropic Claude |
| Embeddings | OpenAI text-embedding-3-small (or local TF-IDF) |
| Vector DB | ChromaDB |
| Parsing | Python AST + Regex (multi-language) |
| Graph Analysis | NetworkX |
| Visualization | Plotly |
| Frontend | Streamlit |

## Running Tests

```bash
pytest tests/ -v
```

## Docker

```bash
cd docker
docker-compose up --build
```

---

## Supported Languages

Python, JavaScript, TypeScript, Java, Go, Rust, C++, C, C#, Ruby, PHP, Kotlin, Swift

---

## API Reference

Full interactive docs at `http://localhost:8000/docs` (Swagger UI)

| Endpoint | Method | Description |
|---|---|---|
| `/api/ingest-repo` | POST | Ingest a GitHub repository |
| `/api/ask-question` | POST | Ask a natural language question |
| `/api/trace-flow` | POST | Trace an execution flow |
| `/api/get-architecture/{repo_id}` | GET | Get architecture overview |
| `/api/repo-status/{repo_id}` | GET | Check repo index status |
| `/api/list-functions/{repo_id}` | GET | List all known functions |
