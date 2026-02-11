import json
import os

from langsmith import Client
from langsmith.utils import LangSmithConflictError

DATASET_NAME = "novapay-qa-golden"
DATASET_DESCRIPTION = (
    "Golden evaluation set for the NovaPay docs QA RAG chain. "
    "10 curated question/answer pairs covering conflicting info, "
    "split-across-docs, stale-vs-current, documentation gaps, "
    "and straightforward retrieval. Reference outputs generated "
    "by running the real RAG pipeline multiple times and synthesizing."
)

GOLDEN_DATASET_PATH = os.path.join(os.path.dirname(__file__), "golden_dataset.json")


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

    with open(GOLDEN_DATASET_PATH) as f:
        examples = json.load(f)

    client.create_examples(
        inputs=[ex["inputs"] for ex in examples],
        outputs=[ex["outputs"] for ex in examples],
        dataset_id=dataset.id,
    )
    print(f"  Added {len(examples)} examples from {GOLDEN_DATASET_PATH}")
