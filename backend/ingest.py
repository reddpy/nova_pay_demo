"""Document ingestion script for NovaPay docs into ChromaDB."""

import os
import re
import sys

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Allow running as `python -m backend.ingest` or `python backend/ingest.py`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL


def extract_title(content: str, filename: str) -> str:
    """Extract the first heading from markdown content, or use the filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return filename.replace(".md", "").replace("-", " ").title()


def ingest_docs():
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    docs_dir = os.path.abspath(docs_dir)

    if not os.path.exists(docs_dir):
        print(f"Error: docs directory not found at {docs_dir}")
        sys.exit(1)

    print(f"Loading documents from {docs_dir}...")

    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents")

    # Add metadata
    for doc in documents:
        rel_path = os.path.relpath(doc.metadata["source"], docs_dir)
        rel_path = rel_path.replace("\\", "/")  # normalize for Windows
        category = rel_path.split("/")[0] if "/" in rel_path else "general"
        title = extract_title(doc.page_content, os.path.basename(rel_path))

        doc.metadata["source"] = rel_path
        doc.metadata["category"] = category
        doc.metadata["title"] = title

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    # Create embeddings and store in ChromaDB
    print(f"Creating embeddings with {EMBEDDING_MODEL}...")
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    persist_dir = os.path.abspath(CHROMA_PERSIST_DIR)
    print(f"Storing in ChromaDB at {persist_dir}...")

    # Clear existing collection if it exists
    if os.path.exists(persist_dir):
        try:
            import chromadb
            client = chromadb.PersistentClient(path=persist_dir)
            try:
                client.delete_collection(COLLECTION_NAME)
            except ValueError:
                pass
            print("Cleared existing ChromaDB collection")
        except Exception:
            import shutil
            shutil.rmtree(persist_dir, ignore_errors=True)
            print("Cleared existing ChromaDB data")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=persist_dir,
    )

    print(f"\nIngestion complete!")
    print(f"  Documents: {len(documents)}")
    print(f"  Chunks:    {len(chunks)}")
    print(f"  Stored in: {persist_dir}")

    # Verify
    count = vectorstore._collection.count()
    print(f"  Verified:  {count} vectors in collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    ingest_docs()
