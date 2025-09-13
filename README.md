# codex-test

An Informatica mapping-to-SQL converter. This CLI reads Informatica IDMC (JSON) workflow documents and generates ANSI SQL for each mapping using an LLM (OpenAI). It can print SQL to stdout or write a single SQL file per input.

## Requirements
- Python 3.11+
- `uv` installed (https://docs.astral.sh/uv/)

## Quick Start
```bash
# Create and sync a local environment
make bootstrap

# Run the converter (LLM-powered; prints ANSI SQL for each mapping)
make run ARGS=path/to/workflow.json # or: uv run python -m codex_test path/to/workflow.json
codex-test path/to/workflow.json    # installed via editable package

# Run checks
make fmt && make lint && make typecheck
make test             # or: make coverage
```

## LLM-powered Conversion
- Provider: OpenAI (default model `OPENAI_MODEL` env, fallback `gpt-5-mini`)
- Auth/Config: set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in your environment or copy `.env.example` to `.env` and set them there (loaded in dev if `python-dotenv` is installed).
- CLI:
  - `codex-test path/to/workflow.json` → prints model-generated SQL for IDMC JSON
  - `codex-llm path/to/workflow.json` → equivalent direct LLM entrypoint (advanced options; `--model` overrides `OPENAI_MODEL`)

### Agents-based CLI (OpenAI Agents SDK)
- Command: `codex-agents path/to/workflow.json [--model MODEL]`
- Uses the OpenAI Agents SDK with a simple file-reading tool to load the workflow JSON and emit ANSI SQL.
- Env: `OPENAI_API_KEY` (required), `OPENAI_MODEL` (optional; defaults to `gpt-5-mini` for this CLI)

## Usage
- Module: `codex_test`
- CLI: `codex-test`
- Example:
  - `codex-test path/to/workflow.json` → emits SQL per mapping on stdout (via OpenAI)
  - `codex-test path/to/workflow.json --output-dir output/` → writes `<stem>.sql` with all generated SQL

## Informatica Conversion
- **Input formats:**
  - IDMC workflow JSON
- **What it does:**
  - Parses mappings and converts them to ANSI-SQL statements.
  - Generates `INSERT INTO ... SELECT ...` for each mapping/target.
- **LLM behavior:**
  - Accepts `source`/`sources` and `target`/`targets` keys.
  - Reads fields from varied shapes: `fields`, `columns`, `ports`, `schema.fields`, `items` (recursively flattened and de-duplicated, order preserved).
-  - May use JOIN ... USING when sources share columns; otherwise CROSS JOIN where needed.
-  - If a target column is not found, may project `NULL AS <col>`.
- **Output options:**
  - Print SQL to stdout (default).
  - Write files with `--output-dir output/` (writes `<stem>.sql`).

### Examples
- Simple (IDMC JSON):
```json
{
  "mappings": [
    {
      "name": "m_simple",
      "source": {"name": "SRC_TABLE", "fields": ["id", "name"]},
      "target": {"name": "TGT_TABLE", "fields": ["id", "name"]}
    }
  ]
}
```

- Output (generated SQL; output may vary slightly):
```sql
-- Mapping: m_simple -> TGT_TABLE
INSERT INTO TGT_TABLE (id, name)
SELECT id, name
FROM SRC_TABLE;
```

- Multi-source join (IDMC JSON):
```json
{
  "mappings": [
    {
      "name": "m_join",
      "sources": [
        {"name": "SRC_A", "fields": ["id", "name"]},
        {"name": "SRC_B", "fields": ["id", "amount"]}
      ],
      "target": {"name": "TGT", "fields": ["id", "name", "amount"]}
    }
  ]
}
```

- Output (generated SQL; output may vary slightly):
```sql
-- Mapping: m_join -> TGT
INSERT INTO TGT (id, name, amount)
SELECT id, SRC_A.name, SRC_B.amount
FROM SRC_A
JOIN SRC_B USING (id);
```

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
