import asyncio
import os

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langsmith import Client
from langsmith.utils import LangSmithConflictError

from config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    LLM_MODEL,
    PROMPT_NAME,
    RETRIEVER_K,
)

DATASET_NAME = "novapay-qa-golden"
DATASET_DESCRIPTION = (
    "Golden evaluation set for the NovaPay docs QA RAG chain. "
    "10 curated question/answer pairs covering conflicting info, "
    "split-across-docs, stale-vs-current, documentation gaps, "
    "and straightforward retrieval. Reference outputs generated "
    "by running the real RAG pipeline multiple times and synthesizing."
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
    """Run the real retriever against ChromaDB and format the context string."""
    persist_dir = os.path.abspath(CHROMA_PERSIST_DIR)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVER_K})
    docs = retriever.invoke(question)

    # Same format as rag_chain.format_context()
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[Document {i}: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


async def _generate_samples(question: str, context: str, chain, n: int) -> list[str]:
    """Generate n answers for the same question + context in parallel."""
    tasks = [chain.ainvoke({"context": context, "question": question}) for _ in range(n)]
    responses = await asyncio.gather(*tasks)
    return [r.content for r in responses]


async def _synthesize(question: str, samples: list[str], llm: ChatOpenAI) -> str:
    """Synthesize multiple answers into one reference answer."""
    numbered = "\n\n".join(
        f"--- Response {i + 1} ---\n{s}" for i, s in enumerate(samples)
    )
    prompt = SYNTHESIS_PROMPT.format(n=len(samples), question=question, responses=numbered)
    response = await llm.ainvoke(prompt)
    return response.content


async def _build_examples() -> tuple[list[dict], list[dict]]:
    """Retrieve context, generate N samples, and synthesize for each question."""
    ls_client = Client()
    prompt = ls_client.pull_prompt(f"{PROMPT_NAME}:latest")
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0)
    chain = prompt | llm

    inputs_list = []
    outputs_list = []

    for i, question in enumerate(QUESTIONS, 1):
        print(f"  [{i}/{len(QUESTIONS)}] {question}")

        # 1. Retrieve real context from ChromaDB
        context = _retrieve_context(question)

        # 2. Generate N_SAMPLES answers in parallel
        print(f"           Generating {N_SAMPLES} samples...")
        samples = await _generate_samples(question, context, chain, N_SAMPLES)

        # 3. Synthesize into one reference answer
        print(f"           Synthesizing reference answer...")
        reference = await _synthesize(question, samples, llm)

        inputs_list.append({"question": question, "context": context})
        outputs_list.append({"answer": reference})

    return inputs_list, outputs_list


def seed_datasets() -> None:
    client = Client()

    try:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description=DATASET_DESCRIPTION,
        )
        print(f"  Created dataset: '{DATASET_NAME}' (id={dataset.id})")
    except LangSmithConflictError:
        print(f"  '{DATASET_NAME}' already exists, skipping")
        return

    inputs_list, outputs_list = asyncio.run(_build_examples())

    client.create_examples(
        inputs=inputs_list,
        outputs=outputs_list,
        dataset_id=dataset.id,
    )
    print(f"  Added {len(QUESTIONS)} examples")
