#!/bin/bash
# Check for known security vulnerabilities in dependencies.
# Uses pip-audit against the PyPI/OSV vulnerability database.
#
# Install: uv sync --dev
# Usage: ./scripts/check_dependencies.sh

set -euo pipefail

echo "Checking dependencies for known vulnerabilities..."
echo ""

# Check pip-audit is available
if command -v uv &> /dev/null; then
    PIP_AUDIT="uv run pip-audit"
elif command -v pip-audit &> /dev/null; then
    PIP_AUDIT="pip-audit"
elif [ -f "./venv/bin/pip-audit" ]; then
    PIP_AUDIT="./venv/bin/pip-audit"
else
    echo "ERROR: pip-audit not found."
    echo "Install it: uv sync --dev"
    exit 1
fi

# Run pip-audit on installed packages
if $PIP_AUDIT 2>&1; then
    echo ""
    echo "✅ Dependency audit PASSED — no known vulnerabilities found."
    exit 0
else
    echo ""
    echo "❌ Dependency audit FAILED — vulnerabilities found above."
    echo "Run 'uv lock --upgrade-package <pkg>' to update affected packages."
    exit 1
fi
