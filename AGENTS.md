# AGENTS.md

## Build/Test Commands
- **Install deps**: `poetry install`
- **Run all tests**: `poetry run pytest`
- **Run single test**: `poetry run pytest tests/test_generator.py::test_generate_clients -k "hello_world"`
- **Run tests in parallel**: `poetry run pytest -n auto`
- **Update approvals**: `poetry run poe update-approvals`

## Lint/Format Commands
- **Lint**: `poetry run ruff check --fix`
- **Format**: `poetry run ruff format`
- **Type check**: `poetry run mypy`
- **Pre-commit**: `poetry run pre-commit run --all-files`

## Code Style
- Python 3.10+, strict mypy with full type annotations required
- Line length: 120 chars; use `ruff` for linting/formatting, `mypy` for type checking
- Imports: use `isort` ordering (via ruff), group stdlib/third-party/local
- Naming: snake_case for functions/variables, PascalCase for classes, prefix private with `_`
- Use `pathlib.Path` instead of `os.path`; use dataclasses with `kw_only=True`
- Tests use pytest with parametrize; test files in `tests/` mirror `src/` structure
