import os
from dotenv import load_dotenv

load_dotenv()

# LLM
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ChromaDB
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
COLLECTION_NAME = "novapay_docs"

# RAG
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 4

# Prompt Hub
PROMPT_NAME = os.getenv("PROMPT_NAME", "novapay-qa-prompt")
PROMPT_TAG = os.getenv("PROMPT_TAG", "prod")

# LangSmith
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "novapay-docs-qa")
