#!/bin/bash
# Verify README and CLAUDE.md claims against live data.
# Catches stale test counts, tool counts, and coverage stats.
#
# Usage: ./scripts/check_readme_claims.sh

set -euo pipefail

ERRORS=0
README="README.md"
CLAUDE_MD=".claude/CLAUDE.md"
SERVER="src/omnifocus_mcp/server_fastmcp.py"

echo "Checking README and CLAUDE.md claims..."
echo ""

# --- Check 1: Tool count ---
echo "--- Check 1: MCP tool count ---"
ACTUAL_TOOLS=$(grep -c "@mcp.tool()" "$SERVER")
README_TOOLS=$(grep -oE 'Tools \([0-9]+\)' "$README" | grep -oE '[0-9]+')

if [ "$ACTUAL_TOOLS" != "$README_TOOLS" ]; then
    echo "ERROR: README says Tools ($README_TOOLS) but server has $ACTUAL_TOOLS @mcp.tool() decorators"
    ERRORS=$((ERRORS + 1))
else
    echo "OK: Tool count matches ($ACTUAL_TOOLS)"
fi
echo ""

# --- Check 2: Unit test count ---
echo "--- Check 2: Unit test count ---"
ACTUAL_UNIT=$(uv run pytest tests/ -q 2>/dev/null | tail -1 | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+')
README_UNIT=$(grep -oE '[0-9]+ unit tests' "$README" | grep -oE '[0-9]+')

if [ "$ACTUAL_UNIT" != "$README_UNIT" ]; then
    echo "ERROR: README says $README_UNIT unit tests but pytest collects $ACTUAL_UNIT"
    ERRORS=$((ERRORS + 1))
else
    echo "OK: Unit test count matches ($ACTUAL_UNIT)"
fi
echo ""

# --- Check 3: Coverage badge ---
echo "--- Check 3: Coverage badge ---"
BADGE_PCT=$(grep -oE 'coverage-[0-9]+' "$README" | sed 's/coverage-//' || true)
CLAUDE_PCT=$(grep -oE 'Coverage:.* [0-9]+%' "$CLAUDE_MD" | grep -oE '[0-9]+%' | sed 's/%//' || true)

if [ -n "$BADGE_PCT" ] && [ -n "$CLAUDE_PCT" ]; then
    if [ "$BADGE_PCT" != "$CLAUDE_PCT" ]; then
        echo "ERROR: README badge says ${BADGE_PCT}% but CLAUDE.md says ${CLAUDE_PCT}%"
        ERRORS=$((ERRORS + 1))
    else
        echo "OK: Coverage claims consistent (${BADGE_PCT}%)"
    fi
else
    echo "WARNING: Could not extract coverage from README or CLAUDE.md"
fi
echo ""

# --- Check 4: CLAUDE.md unit test count ---
echo "--- Check 4: CLAUDE.md test counts ---"
CLAUDE_UNIT=$(grep -oE '[0-9]+ unit' "$CLAUDE_MD" | head -1 | grep -oE '[0-9]+')

if [ -n "$CLAUDE_UNIT" ] && [ "$ACTUAL_UNIT" != "$CLAUDE_UNIT" ]; then
    echo "ERROR: CLAUDE.md says $CLAUDE_UNIT unit but pytest collects $ACTUAL_UNIT"
    ERRORS=$((ERRORS + 1))
else
    echo "OK: CLAUDE.md unit test count matches ($CLAUDE_UNIT)"
fi
echo ""

# --- Summary ---
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ All README/CLAUDE.md claims verified!"
    exit 0
else
    echo "❌ $ERRORS claim(s) out of date. Update README.md and/or .claude/CLAUDE.md."
    exit 1
fi
