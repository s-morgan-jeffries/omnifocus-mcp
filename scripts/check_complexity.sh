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

echo "1. Cyclomatic Complexity (src/omnifocus_mcp/omnifocus_connector.py)"
echo "----------------------------------------------------------------"
echo "Ratings: A (1-5), B (6-10), C (11-20), D (21-50), F (51+)"
echo ""
$RADON cc src/omnifocus_mcp/omnifocus_connector.py -s -a --total-average
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
#   - get_tasks: CC ≤ 25 (24 current - orchestrator after full extraction)
#   - _post_process_tasks: CC ≤ 29 (28 current - normalization + Python-side filtering)
#   - _build_task_filter_checks: CC ≤ 55 (54 current - 12+ filter types × per-task + batch variants)
#   - update_task: CC ≤ 54 (53 current - extensive property handling)
#   - update_tasks: CC ≤ 47 (46 current - batch property handling)
#   - update_projects: CC ≤ 35 (34 current)
#   - get_projects: CC ≤ 36 (35 current - v0.9.0 added stalled_only, completedByChildren, effective dates)
#   - update_project: CC ≤ 33 (32 current - v0.9.0 added completed_by_children, next_review_date)
#   - _filter_projects_by_conditions: CC ≤ 25 (24 current)
#   - create_task: CC ≤ 22 (21 current - many optional parameters with date handling)
#   - _format_task: CC ≤ 26 (25 current)
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
                if name == 'get_tasks' and cc <= 25:
                    continue
                elif name == '_post_process_tasks' and cc <= 29:
                    continue
                elif name == '_build_task_filter_checks' and cc <= 55:
                    continue
                elif name == 'update_task' and cc <= 54:
                    continue
                elif name == 'get_projects' and cc <= 36:
                    continue
                elif name == 'update_project' and cc <= 33:
                    continue
                elif name == '_filter_projects_by_conditions' and cc <= 25:
                    continue
                elif name == 'create_task' and cc <= 22:
                    continue
                elif name == 'update_tasks' and cc <= 47:
                    continue
                elif name == '_format_task' and cc <= 26:
                    continue
                elif name == 'update_projects' and cc <= 35:
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
    echo "  - get_tasks(): CC ≤ 25 (current: 24)"
    echo "  - _post_process_tasks(): CC ≤ 29 (current: 28)"
    echo "  - _build_task_filter_checks(): CC ≤ 55 (current: 54)"
    echo "  - update_task(): CC ≤ 54 (current: 53)"
    echo "  - get_projects(): CC ≤ 36 (current: 35)"
    echo "  - update_project(): CC ≤ 33 (current: 32)"
    echo ""
    echo "See docs/reference/HYGIENE_CHECK_CRITERIA.md for details."
    exit 1
fi

echo "✅ PASS: All functions within complexity limits"
echo ""
echo "Documented high complexity functions (AppleScript constraints):"
echo "  - get_tasks(): CC ≤ 25 (orchestrator after full extraction)"
echo "  - _post_process_tasks(): CC ≤ 29 (normalization + Python-side filtering)"
echo "  - _build_task_filter_checks(): CC ≤ 55 (12+ filter types × per-task + batch variants)"
echo "  - update_task(): CC ≤ 54 (extensive property handling)"
echo "  - get_projects(): CC ≤ 36 (v0.9.0: stalled_only, completedByChildren, effective dates)"
echo "  - update_project(): CC ≤ 33 (v0.9.0: completed_by_children, next_review_date)"
echo "  - All other functions: CC ≤ 20"
echo ""
echo "See inline documentation in omnifocus_connector.py for rationale."
echo ""
exit 0
