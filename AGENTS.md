# Repository Guidelines

## Project Structure & Module Organization
- Python source in `src/<package_name>/`; tests in `tests/`; developer utilities in `scripts/`; docs in `docs/`; assets in `assets/`.
- Mirror modules in `tests/` (e.g., `src/app/utils.py` → `tests/app/test_utils.py`). Keep packages explicit with `__init__.py`.
- Keep modules small and single-purpose; separate layers (domain, adapters, cli/web) for clarity.

## Build, Test, and Development Commands
- Python 3.11+ recommended. Use `uv` for environment and dependency management.
- Create env: `uv venv`; install deps (incl. dev extras): `uv sync --extra dev`.
- Lint/format: `uv run ruff check .` and `uv run black .` (or `uv run ruff format .`).
- Type-check: `uv run mypy src`.
- Tests: `uv run pytest -q` or with coverage `uv run pytest -q --cov=src --cov-report=term-missing`.
- Make targets wrap these: `make bootstrap | fmt | lint | typecheck | test | coverage | run | lock | sync`.
- Generate/update lockfile: `make lock` (creates/refreshes `uv.lock` and syncs the env). Use this after changing deps.

## Coding Style & Naming Conventions
- Follow PEP 8; 4-space indentation; max line length 88 (Black default).
- Names: packages/modules `snake_case`; classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_SNAKE_CASE`.
- Type hints (PEP 484) for all public functions; concise PEP 257 docstrings (Google-style acceptable).

## Testing Guidelines
- Use `pytest`. Name tests `test_*.py`; place shared fixtures in `tests/conftest.py`.
- Mirror `src/` structure; separate `tests/unit/` and `tests/integration/` if helpful.
- Target ≥85% coverage on changed code; include error paths and edge cases. Prefer deterministic tests; mock I/O and network.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
  - Example: `feat(api): add pagination to list_items()`.
- One logical change per PR; include clear description, rationale, linked issues (`Closes #<id>`), and relevant logs/screenshots.
- Install hooks: `uv run pre-commit install` (runs Black/Ruff/Mypy on commit if configured). Ensure CI green before request review.

## Branching Strategy
- Never commit directly to `main` and never develop on `main`.
- Create a feature branch from the latest `main` for every change (e.g., `feat/…`, `fix/…`, `docs/…`).
- Open a PR from the feature branch into `main`; request review before merge.
- Keep PRs focused and small; one logical change per PR.

## Security & Configuration Tips
- Do not commit secrets. Provide `.env.example`; load via `python-dotenv` in dev if needed.
- Pin dependencies in `requirements*.txt` or lock with your chosen tool; update regularly.
- Validate inputs at boundaries; avoid `eval/exec`; treat filesystem and network as untrusted.

## Notes for This Repository
- If starting from empty, scaffold `src/`, `tests/`, and `scripts/` as above and add a minimal `pyproject.toml` or `requirements*.txt` to standardize setup.
