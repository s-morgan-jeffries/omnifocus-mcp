.PHONY: test test-unit test-integration test-verbose install clean help

help:
	@echo "Available targets:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make clean            - Remove cache and build artifacts"

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

test:
	./venv/bin/pytest

test-unit:
	./venv/bin/pytest test_omnifocus_client.py test_server.py

test-integration:
	./venv/bin/pytest test_integration.py

test-verbose:
	./venv/bin/pytest -v --tb=long

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
