"""Delete all LangSmith resources: prompts, datasets, experiments, annotation queues, and tracing projects."""

import time

from langsmith import Client
from langsmith.utils import LangSmithNotFoundError, LangSmithRateLimitError

RATE_LIMIT_WAIT = 30  # seconds to wait on 429
DELETE_DELAY = 2  # seconds between every delete call to stay under rate limit


def _delete_with_retry(fn, label: str, retries: int = 3) -> None:
    """Call *fn* with retry on rate-limit errors. Skips on final failure."""
    for attempt in range(1, retries + 1):
        try:
            fn()
            print(f"  Deleted {label}")
            time.sleep(DELETE_DELAY)
            return
        except LangSmithNotFoundError:
            print(f"  Already deleted: {label}")
            return
        except LangSmithRateLimitError:
            if attempt < retries:
                wait = RATE_LIMIT_WAIT * attempt
                print(f"  Rate-limited on {label}, waiting {wait}s (attempt {attempt}/{retries})...")
                time.sleep(wait)
            else:
                print(f"  Skipping {label} after {retries} rate-limit failures")
                return


def teardown() -> None:
    client = Client()

    # Prompts
    print("\n[Prompts]")
    resp = client.list_prompts(is_public=False)
    for prompt in resp.repos:
        _delete_with_retry(
            lambda p=prompt: client.delete_prompt(prompt_identifier=p.repo_handle),
            f"prompt: {prompt.repo_handle}",
        )

    # Datasets (cascade-deletes associated experiments)
    print("\n[Datasets]")
    for dataset in client.list_datasets():
        _delete_with_retry(
            lambda d=dataset: client.delete_dataset(dataset_id=d.id),
            f"dataset: {dataset.name}",
        )

    # Tracing projects (skip experiment projects — already removed with datasets)
    print("\n[Tracing Projects]")
    for project in client.list_projects():
        if project.reference_dataset_id is not None:
            continue
        _delete_with_retry(
            lambda p=project: client.delete_project(project_name=p.name),
            f"project: {project.name}",
        )

    # Annotation Queues
    print("\n[Annotation Queues]")
    for queue in client.list_annotation_queues():
        _delete_with_retry(
            lambda q=queue: client.delete_annotation_queue(queue_id=q.id),
            f"annotation queue: {queue.name}",
        )

    print("\nTeardown complete.")
