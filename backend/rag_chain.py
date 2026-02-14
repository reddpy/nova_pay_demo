"""Core RAG pipeline for NovaPay Docs Q&A."""

import logging
import os
import sys
from typing import AsyncIterator

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import langsmith as ls

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    LLM_MODEL,
    PROMPT_NAME,
    PROMPT_TAG,
    RETRIEVER_K,
)

logger = logging.getLogger(__name__)

# Server-side conversation history, keyed by session_id
_history_store: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _history_store:
        _history_store[session_id] = InMemoryChatMessageHistory()
    return _history_store[session_id]

def _get_vectorstore() -> Chroma:
    """Initialize the ChromaDB vector store."""
    persist_dir = os.path.abspath(CHROMA_PERSIST_DIR)
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(
            f"ChromaDB not found at {persist_dir}. "
            "Run `python -m backend.ingest` first to ingest documents."
        )
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )


def _get_chain():
    """Pull prompt + model from LangSmith Hub."""
    client = ls.Client()
    prompt_ref = f"{PROMPT_NAME}:{PROMPT_TAG}"
    chain = client.pull_prompt(prompt_ref, include_model=True)
    logger.info(f"Loaded chain from Hub: {prompt_ref}")
    return chain


@tool
def list_documents() -> str:
    """List all available documents in the NovaPay knowledge base, organized by category."""
    vectorstore = _get_vectorstore()
    collection = vectorstore._collection
    all_metadata = collection.get()["metadatas"]

    docs_by_category: dict[str, set[str]] = {}
    for meta in all_metadata:
        category = meta.get("category", "General")
        source = meta.get("source", "unknown")
        docs_by_category.setdefault(category, set()).add(source)

    lines = ["**Available NovaPay Documentation:**\n"]
    for category in sorted(docs_by_category):
        lines.append(f"### {category}")
        for title in sorted(docs_by_category[category]):
            lines.append(f"- {title}")
        lines.append("")

    return "\n".join(lines)


ROUTE_SYSTEM_PROMPT = (
    "You are a routing assistant for NovaPay documentation. "
    "You have access to a `list_documents` tool that lists every document in the knowledge base. "
    "ONLY call the tool when the user EXPLICITLY asks to list, browse, or see all available documents "
    "(e.g. 'what documents do you have?', 'show me available docs', 'list all topics'). "
    "Do NOT call the tool for ambiguous, short, or follow-up messages like 'yes', 'tell me more', 'go on', 'thanks', etc. "
    "For EVERYTHING else — including follow-ups, clarifications, and content questions — reply with the single word RAG."
)


@ls.traceable(name="route_query", run_type="chain")
async def route_query(question: str, history: list | None = None) -> AIMessage:
    """Ask the LLM whether to use a tool or fall through to RAG."""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0).bind_tools([list_documents])
    messages = [SystemMessage(content=ROUTE_SYSTEM_PROMPT)]
    if history:
        messages.extend(history)
    messages.append(HumanMessage(content=question))
    response = await llm.ainvoke(messages)
    return response


@ls.traceable(name="retrieve_documents", run_type="retriever")
def retrieve_documents(question: str, metadata: dict | None = None) -> list[Document]:
    """Retrieve relevant documents from the vector store."""
    vectorstore = _get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
    docs = retriever.invoke(question)
    return docs


@ls.traceable(name="format_context", run_type="chain")
def format_context(docs: list[Document]) -> str:
    """Format retrieved documents into a context string."""
    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        context_parts.append(f"[Document {i}: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(context_parts)



def _extract_sources(docs: list[Document]) -> list[dict]:
    """Extract source information from documents."""
    sources = []
    seen = set()
    for doc in docs:
        source_file = doc.metadata.get("source", "unknown")
        if source_file not in seen:
            seen.add(source_file)
            snippet = doc.page_content[:200].strip()
            if len(doc.page_content) > 200:
                snippet += "..."
            sources.append({"file": source_file, "snippet": snippet})
    return sources


@ls.traceable(name="rag_stream", run_type="chain")
async def stream_rag_response(
    question: str, metadata: dict | None = None
) -> AsyncIterator[dict]:
    """Streaming RAG pipeline with tool-calling routing."""
    # Propagate session_id to all child runs for proper thread grouping
    session_id = (metadata or {}).get("thread_id")
    ls_extra = {"metadata": {"session_id": session_id}} if session_id else {}

    # Load server-side history and record the user message
    history = get_session_history(session_id) if session_id else None
    if history:
        history.add_user_message(question)

    history_messages = history.messages[:-1] if history else None  # exclude current question

    route_response = await route_query(question, history=history_messages, langsmith_extra=ls_extra)

    if route_response.tool_calls:
        tool_call = route_response.tool_calls[0]
        tool_result = list_documents.invoke(tool_call["args"])

        llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
        messages = [
            SystemMessage(content="Present the tool results to the user in a helpful way."),
            HumanMessage(content=question),
            route_response,
            ToolMessage(content=tool_result, tool_call_id=tool_call["id"]),
        ]
        full_response = ""
        async for chunk in llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield {"type": "token", "content": chunk.content}

        if history:
            history.add_ai_message(full_response)

        yield {"type": "sources", "content": []}
        yield {"type": "done"}
        return

    docs = retrieve_documents(question, metadata=metadata, langsmith_extra=ls_extra)
    context = format_context(docs, langsmith_extra=ls_extra)

    chain = _get_chain()

    chain_input = {"context": context, "question": question}
    if history_messages:
        chain_input["history"] = history_messages

    full_response = ""
    async for chunk in chain.astream(chain_input):
        if chunk.content:
            full_response += chunk.content
            yield {"type": "token", "content": chunk.content}

    if history:
        history.add_ai_message(full_response)

    sources = _extract_sources(docs)
    yield {"type": "sources", "content": sources}
    yield {"type": "done"}
