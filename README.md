# codex-test

A minimal, Python 3.11+ project scaffold with a small CLI, tests, and batteries-included developer tooling. It uses `uv` for fast environment and dependency management, `pytest` for tests, `ruff`/`black` for lint/format, and `mypy` for optional static typing.

## Requirements
- Python 3.11+
- `uv` installed (https://docs.astral.sh/uv/)

## Quick Start
```bash
# Create and sync a local environment
make bootstrap

# Run the app (prints ANSI SQL for each mapping)
# Supports Informatica IDMC (JSON) and PowerCenter (XML)
make run ARGS=path/to/workflow.json # or: uv run python -m codex_test path/to/workflow.json
codex-test path/to/workflow.json    # installed via editable package

# Run checks
make fmt && make lint && make typecheck
make test             # or: make coverage
```

## Usage
- Module: `codex_test`
- CLI: `codex-test`
- Example:
  - `codex-test path/to/workflow.json` → emits SQL per mapping on stdout
  - `codex-test path/to/workflow.json --output-dir out/` → writes one `<mapping>.sql` file per mapping
  - Also accepts PowerCenter XML for backward compatibility

## Informatica Conversion
- **Input formats:**
  - IDMC workflow JSON (auto-detected by `.json` or JSON content)
  - PowerCenter workflow XML (legacy support; auto-detected otherwise)
- **What it does:**
  - Parses mappings and converts them to ANSI-SQL statements.
  - Generates `INSERT INTO ... SELECT ...` for each mapping/target.
- **IDMC features:**
  - Accepts `source`/`sources` and `target`/`targets` keys.
  - Reads fields from varied shapes: `fields`, `columns`, `ports`, `schema.fields`, `items` (recursively flattened and de-duplicated, order preserved).
  - Multiple sources supported:
    - If sources share common column names, generates `JOIN ... USING(common_cols)`.
    - If no common columns are found, uses `CROSS JOIN` and adds a comment note.
  - Multiple targets supported: emits one `INSERT` per target from the same `SELECT`.
  - Column selection prefers target field order; qualifies non-common columns. Missing columns are projected as `NULL AS <col>`.
- **PowerCenter features:**
  - Handles simple cases with a single `Source Definition` and `Target Definition` and their `<FIELD NAME='...'>` entries.
  - For complex transformations (joins, filters, lookups, etc.), emits a commented placeholder `SELECT`.
- **Output options:**
  - Print SQL to stdout (default).
  - Write files with `--output-dir out/` (one `<mapping>.sql` per mapping).

## Limitations
- Advanced Informatica transformations (expressions, filters, lookups, aggregations, conditional logic, etc.) are not currently modeled.
- Join inference relies on identical column names across sources; aliasing or mapping logic is not interpreted.
- Generated SQL is ANSI-oriented and does not apply vendor-specific dialect features.

## Project Structure
```
.
├── src/codex_test/        # Package code (CLI + library)
├── tests/                 # Pytest test suite
├── scripts/               # Helper scripts (dev, test)
├── pyproject.toml         # Project metadata & tooling config
├── Makefile               # Common developer tasks (uv-powered)
├── AGENTS.md              # Contributor guide
└── .pre-commit-config.yaml# Local lint/type hooks
```

## Common Tasks
- `make bootstrap`: Create venv (`uv venv`) and install deps (`uv sync --extra dev`).
- `make fmt` / `make lint`: Format with Black and Ruff; run lint checks.
- `make typecheck`: Run Mypy on `src/`.
- `make test` / `make coverage`: Run tests (optionally with coverage report).
- `make run`: Execute the CLI via module entry point.
- `make lock`: Generate/update `uv.lock` and sync environment.

## Contributing
See `AGENTS.md` for coding style, testing, commit/PR guidance, and security notes. Install Git hooks with: `uv run pre-commit install`.

## License
Add a `LICENSE` file to define the project’s license (e.g., MIT, Apache-2.0). Until then, all rights reserved.
