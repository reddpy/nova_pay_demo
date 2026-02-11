"""Core RAG pipeline for NovaPay Docs Q&A."""

import logging
import os
import sys
from typing import AsyncIterator

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langsmith import traceable

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


def _get_prompt() -> ChatPromptTemplate:
    """Pull prompt from LangSmith Hub."""
    from langsmith import Client

    client = Client()
    prompt = client.pull_prompt(f"{PROMPT_NAME}:{PROMPT_TAG}")
    logger.info(f"Loaded prompt from Hub: {PROMPT_NAME}:{PROMPT_TAG}")
    return prompt


@traceable(name="retrieve_documents")
def retrieve_documents(question: str, metadata: dict | None = None) -> list[Document]:
    """Retrieve relevant documents from the vector store."""
    vectorstore = _get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
    docs = retriever.invoke(question)
    return docs


@traceable(name="format_context")
def format_context(docs: list[Document]) -> str:
    """Format retrieved documents into a context string."""
    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        context_parts.append(f"[Document {i}: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(context_parts)


@traceable(name="generate_answer")
async def generate_answer(
    question: str, context: str, metadata: dict | None = None
) -> str:
    """Generate an answer using the LLM with the retrieved context."""
    prompt = _get_prompt()
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    chain = prompt | llm
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


@traceable(name="rag_query", run_type="chain")
async def rag_query(
    question: str, metadata: dict | None = None
) -> dict:
    """Full RAG pipeline: retrieve, format, generate. Returns complete response."""
    docs = retrieve_documents(question, metadata=metadata)
    context = format_context(docs)
    answer = await generate_answer(question, context, metadata=metadata)
    sources = _extract_sources(docs)
    return {"answer": answer, "sources": sources}


@traceable(name="rag_stream", run_type="chain")
async def stream_rag_response(
    question: str, metadata: dict | None = None
) -> AsyncIterator[dict]:
    """Streaming RAG pipeline. Yields token chunks and then sources."""
    docs = retrieve_documents(question, metadata=metadata)
    context = format_context(docs)

    prompt = _get_prompt()
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0, streaming=True)
    chain = prompt | llm

    async for chunk in chain.astream({"context": context, "question": question}):
        if chunk.content:
            yield {"type": "token", "content": chunk.content}

    sources = _extract_sources(docs)
    yield {"type": "sources", "content": sources}
    yield {"type": "done"}
