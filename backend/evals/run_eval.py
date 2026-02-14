"""Run a correctness evaluation experiment against the golden dataset.

Usage:
    cd backend && uv run python -m evals.run_eval                        # defaults from config
    cd backend && uv run python -m evals.run_eval --tag staging          # override prompt tag
    cd backend && uv run python -m evals.run_eval --prefix my-experiment # override experiment prefix
"""

import argparse
import os
import sys

from langchain_core.messages import AIMessage
from langsmith import Client, evaluate
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import PROMPT_NAME, PROMPT_TAG

DATASET_NAME = "novapay-qa-golden"


class AnswerOutput(BaseModel):
    """Answer to the question based on the provided context."""
    content: str = Field(description="The answer content")


def make_target(prompt_ref: str):
    """Return a target function closed over the prompt ref."""
    def target(inputs: dict) -> dict:
        client = Client()
        chain = client.pull_prompt(prompt_ref, include_model=True)
        structured_chain = chain.first | chain.last.with_structured_output(
            AnswerOutput, method="json_schema", strict=True
        )

        response = structured_chain.invoke({
            "question": inputs["question"],
            "context": inputs["context"],
            "history": [],
        })
        return {"output": AIMessage(content=response.content)}

    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Run correctness eval")
    parser.add_argument("--tag", default=PROMPT_TAG, help=f"Prompt tag (default: {PROMPT_TAG})")
    parser.add_argument("--prefix", default="baseline", help="Experiment prefix (default: baseline)")
    args = parser.parse_args()

    prompt_ref = f"{PROMPT_NAME}:{args.tag}"
    print(f"Prompt: {prompt_ref} (model config pulled from prompt commit)")
    print(f"Prefix: {args.prefix}")
    print(f"Running correctness eval against '{DATASET_NAME}'...")

    results = evaluate(
        make_target(prompt_ref),
        data=DATASET_NAME,
        experiment_prefix=args.prefix,
    )
    print(f"Experiment complete: {results.experiment_name}")


if __name__ == "__main__":
    main()
