.PHONY: test test-unit test-integration test-verbose install clean complexity help

help:
	@echo "Available targets:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make complexity       - Check code complexity with radon"
	@echo "  make clean            - Remove cache and build artifacts"

install:
	python3 -m venv venv
	./venv/bin/pip install -e ".[dev]"

test:
	./venv/bin/pytest tests/

test-unit:
	./venv/bin/pytest tests/test_omnifocus_client.py tests/test_server_fastmcp.py

test-integration:
	./venv/bin/pytest tests/test_integration_real.py

test-verbose:
	./venv/bin/pytest tests/ -v --tb=long

complexity:
	@./scripts/check_complexity.sh

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
