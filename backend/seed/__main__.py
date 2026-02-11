import sys

from seed.datasets import seed_datasets
from seed.prompts import seed_prompts
from seed.teardown import teardown


def seed() -> None:
    print("=" * 50)
    print("  LangSmith Seed Data")
    print("=" * 50)

    print("\n[Prompts]")
    seed_prompts()

    print("\n[Datasets]")
    seed_datasets()

    print("\n" + "=" * 50)
    print("  Done!")
    print("=" * 50)


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "seed"

    if command == "seed":
        seed()
    elif command == "teardown":
        print("=" * 50)
        print("  LangSmith Teardown")
        print("=" * 50)
        teardown()
        print("\n" + "=" * 50)
        print("  Done!")
        print("=" * 50)
    else:
        print(f"Unknown command: {command}")
        print("Usage: python -m backend.seed [seed|teardown]")
        sys.exit(1)


main()
