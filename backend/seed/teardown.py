"""Delete all LangSmith resources: prompts, datasets, annotation queues, and tracing projects."""

from langsmith import Client


def teardown() -> None:
    client = Client()

    # Prompts
    print("\n[Prompts]")
    resp = client.list_prompts(is_public=False)
    for prompt in resp.repos:
        client.delete_prompt(prompt_identifier=prompt.repo_handle)
        print(f"  Deleted prompt: {prompt.repo_handle}")

    # Datasets
    print("\n[Datasets]")
    for dataset in client.list_datasets():
        client.delete_dataset(dataset_id=dataset.id)
        print(f"  Deleted dataset: {dataset.name}")

    # Annotation Queues
    print("\n[Annotation Queues]")
    for queue in client.list_annotation_queues():
        client.delete_annotation_queue(queue_id=queue.id)
        print(f"  Deleted annotation queue: {queue.name}")

    # Tracing Projects (includes all traces, experiments, monitoring)
    print("\n[Tracing Projects]")
    for project in client.list_projects():
        client.delete_project(project_name=project.name)
        print(f"  Deleted project: {project.name}")

    print("\nTeardown complete.")
