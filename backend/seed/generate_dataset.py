"""One-off script to generate the golden dataset JSON.

Runs the real RAG pipeline (retrieve from ChromaDB + prompt + LLM) multiple times
per question, synthesizes the outputs, and writes the result to golden_dataset.json.

Usage:
    cd backend && uv run python -m seed.generate_dataset
"""

import asyncio
import json
import os
import sys

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langsmith import Client

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    LLM_MODEL,
    PROMPT_NAME,
    RETRIEVER_K,
)

N_SAMPLES = 4

QUESTIONS = [
    "What's the rate limit on the payments API?",
    "What do I need to do before deploying?",
    "How does our auth system work?",
    "How do I configure Stripe webhooks?",
    "How do I access the billing dashboard?",
    "What are the steps for local dev setup?",
    "What happens during a database failover?",
    "What coding standards does NovaPay follow?",
    "How do I handle a payments service outage?",
    "What teams are part of NovaPay engineering?",
]

SYNTHESIS_PROMPT = """\
Below are {n} responses from a documentation QA assistant answering the same question \
with the same retrieved context. Synthesize them into a single reference answer that \
captures the most complete and accurate information across all responses. \
Keep the same style and tone — cite source documents, stay factual, and don't invent information.

Question: {question}

{responses}

Write the synthesized reference answer:"""


def _retrieve_context(question: str) -> str:
    persist_dir = os.path.abspath(CHROMA_PERSIST_DIR)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
    docs = retriever.invoke(question)

    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Document {i}: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


async def _generate_samples(question: str, context: str, chain, n: int) -> list[str]:
    tasks = [chain.ainvoke({"context": context, "question": question}) for _ in range(n)]
    responses = await asyncio.gather(*tasks)
    return [r.content for r in responses]


async def _synthesize(question: str, samples: list[str], llm: ChatOpenAI) -> str:
    numbered = "\n\n".join(
        f"--- Response {i + 1} ---\n{s}" for i, s in enumerate(samples)
    )
    prompt = SYNTHESIS_PROMPT.format(n=len(samples), question=question, responses=numbered)
    response = await llm.ainvoke(prompt)
    return response.content


async def main() -> None:
    ls_client = Client()
    prompt = ls_client.pull_prompt(f"{PROMPT_NAME}:latest")
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    chain = prompt | llm

    examples = []

    for i, question in enumerate(QUESTIONS, 1):
        print(f"[{i}/{len(QUESTIONS)}] {question}")

        context = _retrieve_context(question)

        print(f"  Generating {N_SAMPLES} samples...")
        samples = await _generate_samples(question, context, chain, N_SAMPLES)

        print(f"  Synthesizing reference answer...")
        reference = await _synthesize(question, samples, llm)

        examples.append({
            "inputs": {"question": question, "context": context},
            "outputs": {"answer": reference},
        })

    out_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")
    with open(out_path, "w") as f:
        json.dump(examples, f, indent=2)

    print(f"\nWrote {len(examples)} examples to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
