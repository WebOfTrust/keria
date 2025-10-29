.PHONY: build-wheel install install-dev test

build-wheel:
	@uv build

install:
	@uv sync

install-dev:
	@uv sync --group dev

test:
	@uv run pytest tests/

test-coverage:
	@uv run pytest --cov=src --cov-report=term-missing --cov-report=xml tests/

lint:
	@uv run ruff check src tests

lint-fix:
	@uv run ruff check --fix src tests

format:
	@uv run ruff format

format-check:
	@uv run ruff format --check

clean:
	@rm -rf build/ dist/ *.egg-info/
	@find . -type d -name __pycache__ -delete
	@find . -type f -name "*.pyc" -delete
