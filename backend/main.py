"""FastAPI application for NovaPay Docs Q&A."""

import json
import logging
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langsmith.run_helpers import tracing_context
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.rag_chain import rag_query, stream_rag_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NovaPay Docs Q&A API",
    description="RAG-powered Q&A for NovaPay engineering documentation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str
    metadata: dict | None = None


class SourceItem(BaseModel):
    file: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint. Returns full response as JSON."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    thread_id = (request.metadata or {}).get("thread_id")

    try:
        with tracing_context(metadata={"thread_id": thread_id}):
            result = await rag_query(
                question=request.question,
                metadata=request.metadata,
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Flush traces
    try:
        from langchain_core.tracers import wait_for_all_tracers
        wait_for_all_tracers()
    except Exception:
        pass

    return result


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint. Returns SSE stream."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    thread_id = (request.metadata or {}).get("thread_id")

    async def event_generator():
        try:
            with tracing_context(metadata={"thread_id": thread_id}):
                async for chunk in stream_rag_response(
                    question=request.question,
                    metadata=request.metadata,
                ):
                    yield {"data": json.dumps(chunk)}
        except FileNotFoundError as e:
            yield {
                "data": json.dumps(
                    {"type": "error", "content": str(e)}
                )
            }
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {
                "data": json.dumps(
                    {"type": "error", "content": "Internal server error"}
                )
            }
        finally:
            # Flush traces
            try:
                from langchain_core.tracers import wait_for_all_tracers
                wait_for_all_tracers()
            except Exception:
                pass

    return EventSourceResponse(event_generator())


@app.on_event("startup")
async def startup():
    logger.info("=" * 50)
    logger.info("NovaPay Docs Q&A API starting up")
    logger.info("API available at http://localhost:8000")
    logger.info("Health check: http://localhost:8000/api/health")
    logger.info("=" * 50)

    # Check ChromaDB
    try:
        from backend.rag_chain import _get_vectorstore
        vs = _get_vectorstore()
        count = vs._collection.count()
        logger.info(f"ChromaDB loaded: {count} vectors in collection")
    except FileNotFoundError:
        logger.warning(
            "ChromaDB not found. Run `python -m backend.ingest` to ingest documents."
        )
    except Exception as e:
        logger.warning(f"Could not connect to ChromaDB: {e}")
