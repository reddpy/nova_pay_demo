# NovaPay Docs Portal

A fullstack RAG (Retrieval-Augmented Generation) application for NovaPay's internal engineering documentation. Built with LangChain, FastAPI, ChromaDB, and Next.js — with LangSmith tracing built in.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Next.js React  │────▶│  FastAPI Backend  │────▶│   ChromaDB   │
│    Frontend     │ SSE │  (LangChain RAG)  │     │ (Vector DB)  │
│  localhost:3000 │◀────│  localhost:8000   │     └──────────────┘
└─────────────────┘     └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │    LangSmith     │
                        │   (Tracing &     │
                        │   Observability) │
                        └──────────────────┘
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) (Node.js package manager)
- Docker & Docker Compose (optional, for containerized setup)
- OpenAI API key
- LangSmith API key (free tier at [smith.langchain.com](https://smith.langchain.com))

## Quick Start (Docker)

The easiest way to run everything:

```bash
# 1. Set up env vars
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and LANGCHAIN_API_KEY

# 2. Ingest docs into ChromaDB
docker compose run --rm ingest

# 3. Start the app
docker compose up
```

Open http://localhost:3000 and you're ready.

## Quick Start (Local)

### 1. Set up environment variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   OPENAI_API_KEY=sk-...
#   LANGCHAIN_API_KEY=lsv2_...
```

### 2. Install and run the backend

```bash
cd backend
uv sync
```

### 3. Ingest the docs into ChromaDB

```bash
# From the project root
uv run --project backend python -m backend.ingest
```

This creates a `chroma_db/` directory with embedded document chunks.

### 4. Start the backend

```bash
uv run --project backend uvicorn backend.main:app --reload --port 8000
```

### 5. Install and run the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### 6. Open the app

- **Frontend**: http://localhost:3000
- **Backend health**: http://localhost:8000/api/health
- **LangSmith traces**: https://smith.langchain.com (check the `novapay-docs-qa` project)

## Deliberate Retrieval Challenges

These are intentionally built into the docs to create interesting scenarios during the demo.

### 1. Conflicting Information
- `api/payments-api.md` — rate limit is **1000 requests/min**
- `standards/api-design-guidelines.md` — default rate limit is **500 requests/min**
- **Demo query**: "What's the rate limit on the payments API?"
- **LangSmith demo**: Trace shows both docs retrieved with conflicting values. Fix via Prompt Hub by strengthening conflict-detection instructions, then re-query to show improved answer.

### 2. Information Split Across Docs
- `processes/deployment-process.md` — describes deploy steps, does NOT mention code review requirements
- `processes/code-review-guidelines.md` — states "2 approvals required" and "no deploys from unreviewed branches"
- **Demo query**: "What do I need to do before deploying?"
- **LangSmith demo**: Trace shows whether retriever pulled both docs or missed one. Good for showing retrieval quality and chunk tuning.

### 3. Stale vs Current Info
- `architecture/system-overview.md` (last updated Aug 2024) — references "Auth v1 (JWT)" as current
- `architecture/auth-architecture.md` (last updated Jan 2025) — says Auth v1 was **deprecated Q3 2024**, replaced by Auth v2 (OAuth 2.0 + PKCE)
- **Demo query**: "How does our auth system work?"
- **LangSmith demo**: Trace shows the model receiving contradictory info from stale vs current docs. Good for showing how prompt engineering can instruct the model to prefer newer sources.

### 4. Documentation Gaps
- No docs exist for: **billing service**, **mobile SDK**, **GDPR compliance**, **Stripe webhooks**
- **Demo queries**: "How do I access the billing dashboard?" / "How do I configure Stripe webhooks?"
- **LangSmith demo**: Trace shows irrelevant retrieval results. Model should respond "I don't have documentation on that topic." Good for showing confidence calibration and hallucination prevention.

## Demo Queries (Quick Reference)

| Query | Challenge |
|-------|-----------|
| "What's the rate limit on the payments API?" | Conflicting info |
| "What do I need to do before deploying?" | Split across docs |
| "How does our auth system work?" | Stale vs current |
| "How do I configure Stripe webhooks?" | Documentation gap |
| "How do I access the billing dashboard?" | Documentation gap |

## Project Structure

```
langsmith-demo/
├── docker-compose.yml  # Docker orchestration
├── frontend/           # Next.js React frontend (pnpm)
│   └── Dockerfile
├── backend/            # FastAPI + LangChain backend (uv)
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── main.py         # FastAPI app with SSE streaming
│   ├── rag_chain.py    # RAG pipeline with @traceable spans
│   ├── ingest.py       # Document ingestion into ChromaDB
│   └── config.py       # Configuration
├── docs/               # Fictional NovaPay engineering docs
│   ├── onboarding/     # Getting started guides
│   ├── api/            # API references
│   ├── runbooks/       # Incident runbooks
│   ├── architecture/   # System architecture docs
│   ├── processes/      # Engineering processes
│   └── standards/      # Coding and API standards
└── chroma_db/          # ChromaDB persistent storage (generated)
```

## Tech Stack

**Backend**: Python, FastAPI, LangChain, ChromaDB, OpenAI, LangSmith, **uv**
**Frontend**: Next.js 15, React, TypeScript, Tailwind CSS, **pnpm**
**Infrastructure**: Docker, Docker Compose
**LLM**: GPT-4o-mini (configurable via `LLM_MODEL` env var)
**Embeddings**: text-embedding-3-small
