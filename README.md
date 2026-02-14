# NovaPay Docs Portal

A fullstack RAG (Retrieval-Augmented Generation) application for NovaPay's internal engineering documentation. Built with LangChain, FastAPI, ChromaDB, and Next.js — with LangSmith tracing built in.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Next.js React  │────▶│  FastAPI Backend  │────▶│   ChromaDB   │
│    Frontend     │ SSE │  (LangChain RAG)  │     │ (Vector DB)  │
│    :3000        │◀────│    :8000          │     └──────────────┘
└─────────────────┘     └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │    LangSmith     │
                        │   (Tracing &     │
                        │   Observability) │
                        └──────────────────┘
```

Conversation history is managed **server-side** — the frontend only sends `question` + `thread_id` per request. The backend stores message history in-memory using LangChain's `InMemoryChatMessageHistory`, keyed by `thread_id`.

## Prerequisites

- [Docker & Docker Compose](https://docs.docker.com/get-docker/)
- OpenAI API key
- LangSmith API key (free tier at [smith.langchain.com](https://smith.langchain.com))

## Quick Start

### 1. Set up environment variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   OPENAI_API_KEY=sk-...
#   LANGCHAIN_API_KEY=lsv2_...
```

### 2. Seed LangSmith (first time only)

```bash
./seed.sh      # seed prompts & datasets
./teardown.sh  # wipe all seeded resources
```

Then add the `:prod` tag to the `novapay-qa-prompt` prompt in the LangSmith UI.

### 3. Start the app

```bash
docker compose up
```

### 4. Open the app

- **Frontend**: http://localhost:3000
- **Backend health**: http://localhost:8000/api/health
- **LangSmith traces**: https://smith.langchain.com (check the `novapay-docs-qa` project)

To stop the app, run `docker compose down`. To rebuild after code changes, run `docker compose up --build`.

## Scripts

| Script | Description |
|--------|-------------|
| `./seed.sh` | Push prompts & golden dataset to LangSmith |
| `./teardown.sh` | Delete all seeded LangSmith resources |
| `./generate_dataset.sh` | Regenerate golden dataset reference answers |
| `./run_eval.sh` | Run correctness & off-topic evals against golden dataset |

The eval script accepts optional flags: `./run_eval.sh --tag staging --prefix my-experiment`

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

### 5. Multi-turn Conversations
- Ask a question, then follow up with "tell me more" or "can you elaborate?"
- **Demo**: The backend maintains conversation history per `thread_id`, so follow-ups have full context without the frontend re-sending the entire chat history.
- **LangSmith demo**: Trace inputs for `route_query` and the answer chain show server-side history messages, confirming context is preserved across turns.

## Demo Queries (Quick Reference)

| Query | Challenge |
|-------|-----------|
| "What's the rate limit on the payments API?" | Conflicting info |
| "What do I need to do before deploying?" | Split across docs |
| "How does our auth system work?" | Stale vs current |
| "How do I configure Stripe webhooks?" | Documentation gap |
| "How do I access the billing dashboard?" | Documentation gap |
| "What's the rate limit?" → "tell me more" | Multi-turn context |

## Project Structure

```
nova_pay/
├── docker-compose.yml        # Docker orchestration
├── seed.sh                   # Seed LangSmith resources
├── teardown.sh               # Wipe LangSmith resources
├── generate_dataset.sh       # Regenerate golden dataset
├── run_eval.sh               # Run LangSmith evals
├── frontend/                 # Next.js React frontend (pnpm)
│   ├── Dockerfile
│   └── src/
│       ├── app/page.tsx      # Main chat UI
│       ├── components/       # ChatInterface, MessageBubble, Sidebar, Header, SourceCitation
│       └── lib/
│           ├── api.ts        # SSE streaming client
│           └── types.ts      # TypeScript types
├── backend/                  # FastAPI + LangChain backend (uv)
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── main.py               # FastAPI app with SSE streaming
│   ├── rag_chain.py          # RAG pipeline, routing, server-side history, @traceable spans
│   ├── ingest.py             # Document chunking & ChromaDB ingestion
│   ├── config.py             # Environment & model configuration
│   ├── seed/                 # LangSmith seed scripts (prompts, datasets, teardown)
│   │   └── golden_dataset.json
│   └── evals/                # LangSmith evaluation suite
│       ├── run_eval.py       # Correctness eval runner
│       ├── is_correct_eval_prompt.py
│       └── off_topic_eval_prompt.py
├── docs/                     # Fictional NovaPay engineering docs (17 markdown files)
│   ├── api/                  # payments-api, users-api, notifications-api
│   ├── architecture/         # system-overview, auth-architecture, data-pipeline
│   ├── onboarding/           # first-week-checklist, local-dev-setup, team-structure
│   ├── processes/            # deployment-process, code-review-guidelines, incident-response
│   ├── runbooks/             # database-failover, high-latency-debugging, payments-service-down
│   └── standards/            # api-design-guidelines, coding-standards
└── chroma_db/                # ChromaDB persistent storage (generated at build time)
```

## Tech Stack

**Backend**: Python 3.12, FastAPI, LangChain, ChromaDB, OpenAI, LangSmith, **uv**
**Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, **pnpm**
**Infrastructure**: Docker, Docker Compose
**LLM**: GPT-4o-mini (configurable via `LLM_MODEL` env var)
**Embeddings**: text-embedding-3-small
