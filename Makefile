.PHONY: check test

check:
	uv run ruff check skills tests
	uv run ruff format --check skills tests

test:
	uv run pytest
