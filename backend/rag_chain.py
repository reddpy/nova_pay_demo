"""Core RAG pipeline for NovaPay Docs Q&A."""

import logging
import os
import sys
from typing import AsyncIterator

from langchain_chroma import Chroma
from langchain_core.documents import Document
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
    "If the user is asking what documents or topics are available, call the tool. "
    "For ANY other question (even if it's about documentation content), just reply with the single word RAG."
)


@ls.traceable(name="route_query", run_type="chain")
async def route_query(question: str) -> AIMessage:
    """Ask the LLM whether to use a tool or fall through to RAG."""
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0).bind_tools([list_documents])
    response = await llm.ainvoke([
        SystemMessage(content=ROUTE_SYSTEM_PROMPT),
        HumanMessage(content=question),
    ])
    return response


@ls.traceable(name="retrieve_documents")
def retrieve_documents(question: str, metadata: dict | None = None) -> list[Document]:
    """Retrieve relevant documents from the vector store."""
    vectorstore = _get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
    docs = retriever.invoke(question)
    return docs


@ls.traceable(name="format_context")
def format_context(docs: list[Document]) -> str:
    """Format retrieved documents into a context string."""
    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        context_parts.append(f"[Document {i}: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(context_parts)


@ls.traceable(name="generate_answer")
async def generate_answer(
    question: str, context: str, metadata: dict | None = None
) -> str:
    """Generate an answer using the LLM with the retrieved context."""
    chain = _get_chain()
    response = await chain.ainvoke({"context": context, "question": question})
    return response.content


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
    route_response = await route_query(question)

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
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield {"type": "token", "content": chunk.content}

        yield {"type": "sources", "content": []}
        yield {"type": "done"}
        return

    docs = retrieve_documents(question, metadata=metadata)
    context = format_context(docs)

    chain = _get_chain()

    async for chunk in chain.astream({"context": context, "question": question}):
        if chunk.content:
            yield {"type": "token", "content": chunk.content}

    sources = _extract_sources(docs)
    yield {"type": "sources", "content": sources}
    yield {"type": "done"}
