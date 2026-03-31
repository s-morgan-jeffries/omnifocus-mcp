#!/bin/bash
# Audit AppleScript code in the connector for known unsafe patterns.
# Based on patterns documented in APPLESCRIPT_GOTCHAS.md and CLAUDE.md.
#
# Checks:
#   1. Variable naming conflicts with OmniFocus properties
#   2. Missing _verify_database_safety calls for destructive operations
#   3. Unescaped string interpolation in AppleScript blocks
#   4. Unsafe recurring task completion patterns
#
# Usage: ./scripts/check_applescript_safety.sh

set -euo pipefail

CONNECTOR="src/omnifocus_mcp/omnifocus_connector.py"
WARNINGS=0
ERRORS=0

echo "Running AppleScript safety audit on $CONNECTOR..."
echo ""

# --- Check 1: Variable naming conflicts ---
# OmniFocus property names that should never be used as bare AppleScript variables.
# Safe pattern: "set taskName to" not "set name to"
echo "--- Check 1: Variable naming conflicts ---"

UNSAFE_VARS="set name to |set note to |set status to |set flagged to |set completed to |set sequential to "
if matches=$(grep -n "$UNSAFE_VARS" "$CONNECTOR" 2>/dev/null); then
    echo "WARNING: Possible variable naming conflicts with OmniFocus properties:"
    echo "$matches"
    WARNINGS=$((WARNINGS + $(echo "$matches" | wc -l)))
else
    echo "OK: No variable naming conflicts found."
fi
echo ""

# --- Check 2: Missing safety checks ---
# Every operation in DESTRUCTIVE_OPERATIONS must have a _verify_database_safety call.
echo "--- Check 2: Destructive operation safety coverage ---"

# Extract DESTRUCTIVE_OPERATIONS from the source (stop at closing brace)
DESTRUCTIVE_OPS=$(sed -n '/DESTRUCTIVE_OPERATIONS = {/,/}/p' "$CONNECTOR" | \
    grep -oE "'[a-z_]+'" | tr -d "'" | sort)

MISSING_SAFETY=0
for op in $DESTRUCTIVE_OPS; do
    if ! grep -q "_verify_database_safety('$op')" "$CONNECTOR"; then
        echo "ERROR: Missing _verify_database_safety('$op') call"
        MISSING_SAFETY=$((MISSING_SAFETY + 1))
    fi
done

if [ "$MISSING_SAFETY" -eq 0 ]; then
    echo "OK: All $(echo "$DESTRUCTIVE_OPS" | wc -w | tr -d ' ') destructive operations have safety checks."
else
    ERRORS=$((ERRORS + MISSING_SAFETY))
fi
echo ""

# --- Check 2b: Reverse check — every _verify_database_safety call must use a registered operation ---
echo "--- Check 2b: Reverse safety coverage (calls → set) ---"

CALLED_OPS=$(grep -oE "_verify_database_safety\('[a-z_]+'\)" "$CONNECTOR" | \
    grep -oE "'[a-z_]+'" | tr -d "'" | sort -u)

MISSING_REGISTRATION=0
for op in $CALLED_OPS; do
    if ! echo "$DESTRUCTIVE_OPS" | grep -qw "$op"; then
        echo "ERROR: _verify_database_safety('$op') called but '$op' not in DESTRUCTIVE_OPERATIONS set"
        MISSING_REGISTRATION=$((MISSING_REGISTRATION + 1))
    fi
done

if [ "$MISSING_REGISTRATION" -eq 0 ]; then
    echo "OK: All safety calls use registered operations."
else
    ERRORS=$((ERRORS + MISSING_REGISTRATION))
fi
echo ""

# --- Check 3: Unescaped string interpolation ---
# Look for f-string interpolations of common user-input parameters
# that don't use an _escaped suffix variable.
echo "--- Check 3: Unescaped string interpolation ---"

# Look for bare {name}, {note}, etc. inside AppleScript f-string blocks.
# These indicate user input embedded without _escape_applescript_string().
# Only flag lines that look like AppleScript content (contain tell/set/make/return/etc.)
UNESCAPED=0
while IFS= read -r line; do
    lineno=$(echo "$line" | cut -d: -f1)
    content=$(echo "$line" | cut -d: -f2-)
    # Skip Python-only lines (raise, return, comments, docstrings)
    if echo "$content" | grep -qE "^\s*(#|raise |return |\"\"\"|\.\.\.)"; then
        continue
    fi
    # Only flag lines that look like AppleScript content
    if echo "$content" | grep -qE "(tell |set |make |return |delete |whose |of )"; then
        echo "ERROR: Possible unescaped interpolation at line $lineno: $(echo "$content" | sed 's/^[[:space:]]*//')"
        UNESCAPED=$((UNESCAPED + 1))
    fi
done < <(grep -n '{name}\|{note}\|{tag_name}\|{parent_tag}\|{folder_name}' "$CONNECTOR" 2>/dev/null || true)

if [ "$UNESCAPED" -eq 0 ]; then
    echo "OK: No unescaped string interpolations found."
else
    ERRORS=$((ERRORS + UNESCAPED))
fi
echo ""

# --- Check 4: Unsafe completion pattern ---
# "set completed of X to true" should be "mark complete X" for recurring tasks.
echo "--- Check 4: Recurring task completion safety ---"

if matches=$(grep -n "set completed of.*to true" "$CONNECTOR" 2>/dev/null); then
    echo "WARNING: Found 'set completed of ... to true' — should use 'mark complete' for recurring tasks:"
    echo "$matches"
    WARNINGS=$((WARNINGS + $(echo "$matches" | wc -l)))
else
    echo "OK: No unsafe completion patterns found."
fi
echo ""

# --- Summary ---
echo "========================================="
if [ "$ERRORS" -gt 0 ]; then
    echo "❌ AppleScript safety audit FAILED"
    echo "   $ERRORS error(s), $WARNINGS warning(s)"
    exit 1
elif [ "$WARNINGS" -gt 0 ]; then
    echo "⚠️  AppleScript safety audit PASSED with warnings"
    echo "   $WARNINGS warning(s)"
    exit 0
else
    echo "✅ AppleScript safety audit PASSED"
    exit 0
fi
