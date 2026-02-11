"""Delete all LangSmith resources: prompts, datasets, experiments, annotation queues, and tracing projects."""

from langsmith import Client
from langsmith.utils import LangSmithNotFoundError


def teardown() -> None:
    client = Client()

    # Prompts
    print("\n[Prompts]")
    resp = client.list_prompts(is_public=False)
    for prompt in resp.repos:
        client.delete_prompt(prompt_identifier=prompt.repo_handle)
        print(f"  Deleted prompt: {prompt.repo_handle}")

    # Experiments & Tracing Projects (delete before datasets to avoid orphaned refs)
    # Experiments are projects with a reference_dataset_id; tracing projects are the rest.
    print("\n[Experiments & Tracing Projects]")
    for project in client.list_projects():
        try:
            client.delete_project(project_name=project.name)
            print(f"  Deleted project: {project.name}")
        except LangSmithNotFoundError:
            print(f"  Already deleted: {project.name}")

    # Datasets (after experiments so refs don't break)
    print("\n[Datasets]")
    for dataset in client.list_datasets():
        client.delete_dataset(dataset_id=dataset.id)
        print(f"  Deleted dataset: {dataset.name}")

    # Annotation Queues
    print("\n[Annotation Queues]")
    for queue in client.list_annotation_queues():
        client.delete_annotation_queue(queue_id=queue.id)
        print(f"  Deleted annotation queue: {queue.name}")

    print("\nTeardown complete.")
