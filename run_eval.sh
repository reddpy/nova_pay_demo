#!/usr/bin/env bash
cd "$(dirname "$0")/backend" && uv run python -m evals.run_eval "$@"
