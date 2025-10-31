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
# Use venv python if available, otherwise use system python
if [ -f ./venv/bin/python ]; then
    PYTHON=./venv/bin/python
    RADON=./venv/bin/radon
else
    PYTHON=python
    RADON=radon
fi

if ! $PYTHON -c "import radon" 2>/dev/null; then
    echo "ERROR: radon not installed. Install with:"
    echo "  pip install -e '.[dev]'"
    exit 1
fi

echo "1. Cyclomatic Complexity (src/omnifocus_mcp/omnifocus_client.py)"
echo "----------------------------------------------------------------"
echo "Ratings: A (1-5), B (6-10), C (11-20), D (21-50), F (51+)"
echo ""
$RADON cc src/omnifocus_mcp/omnifocus_client.py -s -a --total-average
echo ""

echo "2. Cyclomatic Complexity (src/omnifocus_mcp/server_fastmcp.py)"
echo "---------------------------------------------------------------"
$RADON cc src/omnifocus_mcp/server_fastmcp.py -s -a --total-average
echo ""

echo "3. Maintainability Index (server_fastmcp.py)"
echo "---------------------------------------------"
echo "Ratings: A (100-20), B (19-10), C (9-0)"
$RADON mi src/omnifocus_mcp/server_fastmcp.py
echo ""

echo "4. Summary of Functions with D or F Complexity"
echo "-----------------------------------------------"
$RADON cc src/omnifocus_mcp/ -n D -s
echo ""

echo "========================================="
echo "Threshold Enforcement"
echo "========================================="
echo ""

# Check for functions with unacceptable complexity
# Documented exceptions with higher limits due to AppleScript constraints:
#   - get_tasks: CC ≤ 70 (68 current - 21 params, extensive filtering)
#   - update_task: CC ≤ 50 (49 current - extensive property handling)
#   - get_projects, update_project, _filter_projects_by_conditions: CC ≤ 30
EXCESSIVE_COMPLEXITY=$($RADON cc src/omnifocus_mcp/ -n D -j | $PYTHON -c "
import sys
import json
try:
    data = json.load(sys.stdin)
    violations = []
    for file_path, items in data.items():
        for item in items:
            if item['type'] in ['function', 'method']:
                cc = item['complexity']
                name = item['name']
                # Documented exceptions with specific limits
                if name == 'get_tasks' and cc <= 70:
                    continue
                elif name == 'update_task' and cc <= 50:
                    continue
                elif name in ['get_projects', 'update_project', '_filter_projects_by_conditions'] and cc <= 30:
                    continue
                # General functions: CC ≤ 20 (C rating or better)
                elif cc <= 20:
                    continue
                # If we reach here, complexity exceeds limits
                violations.append(f\"{file_path}:{item['lineno']} {name}() has CC {cc} (exceeds limit)\")
    if violations:
        print('\\n'.join(violations))
        sys.exit(1)
except Exception as e:
    print(f'Error parsing complexity data: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

if [ $? -ne 0 ]; then
    echo "❌ FAIL: Functions exceed complexity limits:"
    echo "$EXCESSIVE_COMPLEXITY"
    echo ""
    echo "Maximum acceptable complexity:"
    echo "  - General functions: CC ≤ 20 (C rating or better)"
    echo "  - get_tasks(): CC ≤ 70 (current: 68)"
    echo "  - update_task(): CC ≤ 50 (current: 49)"
    echo "  - get_projects(), update_project(): CC ≤ 30"
    echo ""
    echo "See docs/reference/HYGIENE_CHECK_CRITERIA.md for details."
    exit 1
fi

echo "✅ PASS: All functions within complexity limits"
echo ""
echo "Documented high complexity functions (AppleScript constraints):"
echo "  - get_tasks(): CC ≤ 70 (21 parameters, complex filtering)"
echo "  - update_task(): CC ≤ 50 (extensive property handling)"
echo "  - get_projects(), update_project(): CC ≤ 30"
echo "  - All other functions: CC ≤ 20"
echo ""
echo "See inline documentation in omnifocus_client.py for rationale."
echo ""
exit 0
