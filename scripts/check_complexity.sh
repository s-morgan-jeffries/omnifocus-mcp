#!/bin/bash
# Check code complexity using radon
#
# This script analyzes code complexity to help identify areas that may need refactoring.
# Run after making significant code changes to ensure complexity doesn't grow unbounded.

set -e

echo "========================================="
echo "Code Complexity Analysis with Radon"
echo "========================================="
echo ""

# Check if radon is installed
if ! ./venv/bin/python -c "import radon" 2>/dev/null; then
    echo "ERROR: radon not installed. Install with:"
    echo "  pip install -e '.[dev]'"
    exit 1
fi

echo "1. Cyclomatic Complexity (src/omnifocus_mcp/omnifocus_client.py)"
echo "----------------------------------------------------------------"
echo "Ratings: A (1-5), B (6-10), C (11-20), D (21-50), F (51+)"
echo ""
./venv/bin/radon cc src/omnifocus_mcp/omnifocus_client.py -s -a --total-average
echo ""

echo "2. Cyclomatic Complexity (src/omnifocus_mcp/server_fastmcp.py)"
echo "---------------------------------------------------------------"
./venv/bin/radon cc src/omnifocus_mcp/server_fastmcp.py -s -a --total-average
echo ""

echo "3. Maintainability Index (server_fastmcp.py)"
echo "---------------------------------------------"
echo "Ratings: A (100-20), B (19-10), C (9-0)"
./venv/bin/radon mi src/omnifocus_mcp/server_fastmcp.py
echo ""

echo "4. Summary of Functions with D or F Complexity"
echo "-----------------------------------------------"
./venv/bin/radon cc src/omnifocus_mcp/ -n D -s
echo ""

echo "========================================="
echo "Analysis Complete"
echo "========================================="
echo ""
echo "Expected high complexity functions (documented as intentional):"
echo "  - get_tasks() [F]: 21 parameters, complex filtering logic"
echo "  - update_task() [D]: Extensive property handling"
echo "  - get_projects() [D]: Comprehensive data extraction"
echo ""
echo "These functions are intentionally complex due to AppleScript constraints."
echo "See inline documentation in omnifocus_client.py for rationale."
