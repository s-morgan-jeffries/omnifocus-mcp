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
# Prefer uv run, fall back to venv, then system
if command -v uv &> /dev/null; then
    PYTHON="uv run python"
    RADON="uv run radon"
elif [ -f ./venv/bin/python ]; then
    PYTHON=./venv/bin/python
    RADON=./venv/bin/radon
else
    PYTHON=python
    RADON=radon
fi

if ! $PYTHON -c "import radon" 2>/dev/null; then
    echo "ERROR: radon not installed. Install with:"
    echo "  uv sync --dev"
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
# Documented exceptions with higher limits:
#
# Extracted helpers (inherent complexity — CC maps 1:1 to parameter/filter count):
#   - _build_task_filter_checks: CC ≤ 36 (35 current - 12 filter types, batch-only after #368)
#   - _build_update_task_commands: CC ≤ 30 (29 current - 17 updatable fields)
#   - _post_process_tasks: CC ≤ 32 (31 current - normalization + 10 filter steps incl. due/defer/completion/dropped)
#   - _filter_projects_by_conditions: CC ≤ 25 (24 current - 3 conditions × pos/neg matching)
#   - _build_task_source: CC ≤ 23 (22 current - 13 filter types as whose conditions incl. due/defer/planned dates)
#   - _filter_by_date_range: CC ≤ 6 (5 current - delegates to _item_passes_date_check)
#   - _post_process_projects: CC ≤ 27 (26 current - delegates to _compute_project_types, _filter_projects_by_query, _compute_stalled_status + date range filters)
#
# Original functions not yet refactored:
#   - update_projects: CC ≤ 60 (59 current — #417 added flagged/estimated/tags, #506 added review_interval_value/unit)
#   - update_project: CC ≤ 61 (60 current — #417 added flagged/estimated/tags/recurrence, #506 added review_interval_value/unit)
#   - _format_task: CC ≤ 32 (31 current)
#   - create_task: CC ≤ 23 (22 current)
#   - create_project: CC ≤ 25 (24 current — #584 added review_interval_value/unit)
#   - _validate_update_task_params: CC ≤ 19 (18 current)
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
                # Extracted helpers (inherent complexity)
                if name == '_build_task_filter_checks' and cc <= 36:
                    continue
                elif name == '_build_update_task_commands' and cc <= 30:
                    continue
                elif name == '_post_process_tasks' and cc <= 32:
                    continue
                elif name == '_filter_projects_by_conditions' and cc <= 25:
                    continue
                elif name == '_build_task_source' and cc <= 23:
                    continue
                elif name == '_filter_by_date_range' and cc <= 6:
                    continue
                elif name == '_post_process_projects' and cc <= 27:
                    continue
                # Original functions
                elif name == 'update_projects' and cc <= 60:
                    continue
                elif name == 'update_project' and cc <= 61:
                    continue
                elif name == '_format_task' and cc <= 32:
                    continue
                elif name == 'create_task' and cc <= 23:
                    continue
                elif name == 'create_project' and cc <= 25:
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
    echo "  - See documented exceptions in script comments"
    echo ""
    echo "See docs/reference/HYGIENE_CHECK_CRITERIA.md for details."
    exit 1
fi

echo "✅ PASS: All functions within complexity limits"
echo ""
echo "Documented exceptions (see script comments for full list):"
echo "  - Extracted helpers: _build_task_filter_checks (35), _build_update_task_commands (29), _post_process_tasks (31), _build_task_source (22), _post_process_projects (26)"
echo "  - Original functions: update_project (60), update_projects (59), _format_task (31), create_task (22)"
echo "  - All other functions: CC ≤ 20"
echo ""
echo "See inline documentation in omnifocus_connector.py for rationale."
echo ""
exit 0
