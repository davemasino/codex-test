UV := uv

.PHONY: bootstrap fmt lint typecheck test coverage run clean lock sync

bootstrap:
	$(UV) venv
	$(UV) sync --extra dev

fmt:
	$(UV) run black .
	$(UV) run ruff format .

lint:
	$(UV) run ruff check .

typecheck:
	$(UV) run mypy src

test:
	$(UV) run pytest -q

coverage:
	$(UV) run pytest -q --cov=src --cov-report=term-missing

run:
	$(UV) run python -m codex_test

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov

lock:
	$(UV) lock --upgrade
	$(UV) sync --extra dev

sync:
	$(UV) sync --extra dev
