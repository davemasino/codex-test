#!/usr/bin/env bash
set -euo pipefail

uv run pytest -q --cov=src --cov-report=term-missing
