.PHONY: test test-unit test-integration test-e2e test-prod test-verbose install clean complexity audit help

help:
	@echo "Available targets:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests (client layer with real OmniFocus)"
	@echo "  make test-e2e         - Run end-to-end tests (full MCP stack with real OmniFocus)"
	@echo "  make test-prod        - Run production DB tests (OmniAutomation, sandbox folder)"
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
	OMNIFOCUS_TEST_MODE=true OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus" \
	./venv/bin/pytest tests/test_integration_real.py -v

test-e2e:
	OMNIFOCUS_TEST_MODE=true OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus" \
	./venv/bin/pytest tests/test_e2e_real.py -v

test-prod:
	OMNIFOCUS_PROD_TEST=true \
	./venv/bin/pytest tests/test_prod_integration.py -v

test-verbose:
	./venv/bin/pytest tests/ -v --tb=long

complexity:
	@./scripts/check_complexity.sh

audit:
	@./scripts/check_dependencies.sh
	@./scripts/check_applescript_safety.sh

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
