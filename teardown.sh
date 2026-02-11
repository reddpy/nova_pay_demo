#!/usr/bin/env bash
cd "$(dirname "$0")/backend" && uv run python -m seed teardown
