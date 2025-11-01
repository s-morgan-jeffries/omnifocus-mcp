#!/bin/bash
# Check ROADMAP.md sync with closed issues
#
# Verifies that issues closed in the current milestone have been removed
# from active sections of ROADMAP.md (Upcoming Work, Known Bugs, etc.)
#
# Exit codes:
#   0 - ROADMAP.md is synced with closed issues
#   1 - One or more closed issues still appear in ROADMAP.md active sections
#
# Usage:
#   ./scripts/check_roadmap_sync.sh [milestone]
#
# Examples:
#   ./scripts/check_roadmap_sync.sh v0.6.6    # Check specific milestone
#   ./scripts/check_roadmap_sync.sh           # Auto-detect from VERSION

set -e

# Get milestone from argument or detect from VERSION
MILESTONE="${1:-}"

if [ -z "$MILESTONE" ]; then
    # Try to detect from VERSION file
    if [ -f "VERSION" ]; then
        VERSION=$(cat VERSION | tr -d '\n')
        MILESTONE="v$VERSION"
    else
        echo "❌ Error: No milestone specified and VERSION file not found"
        echo "Usage: $0 [milestone]"
        exit 1
    fi
fi

echo "🔍 Checking ROADMAP.md sync for milestone: $MILESTONE"
echo ""

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "⚠️  gh CLI not found. Skipping ROADMAP sync check."
    echo "Install: brew install gh"
    exit 0
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "⚠️  Not in a git repository. Skipping ROADMAP sync check."
    exit 0
fi

# Get all issues closed in the specified milestone
CLOSED_ISSUES=$(gh issue list --milestone "$MILESTONE" --state closed --json number --jq '.[].number' 2>/dev/null || echo "")

if [ -z "$CLOSED_ISSUES" ]; then
    echo "✅ No closed issues found in milestone $MILESTONE"
    exit 0
fi

ISSUE_COUNT=$(echo "$CLOSED_ISSUES" | wc -l | tr -d ' ')
echo "Found $ISSUE_COUNT closed issue(s) in milestone $MILESTONE"
echo ""

# Check if ROADMAP.md exists
ROADMAP_FILE="docs/project/ROADMAP.md"
if [ ! -f "$ROADMAP_FILE" ]; then
    echo "⚠️  ROADMAP.md not found at $ROADMAP_FILE"
    echo "Skipping sync check."
    exit 0
fi

# Define sections to check (issues should NOT appear in these after being closed)
ACTIVE_SECTIONS=(
    "Upcoming Work"
    "Known Bugs"
    "Planned Work"
    "Current Work"
    "In Progress"
)

# Track issues that need to be removed
ISSUES_TO_REMOVE=()

# Check each closed issue
for issue in $CLOSED_ISSUES; do
    # Check if issue appears in any active section
    for section in "${ACTIVE_SECTIONS[@]}"; do
        # Extract content from section to end of file (or next ## header)
        SECTION_CONTENT=$(awk "/^## $section/,/^## /" "$ROADMAP_FILE" 2>/dev/null || echo "")

        if [ -n "$SECTION_CONTENT" ]; then
            # Check if issue number appears in this section
            # Match patterns: #123, (#123), [#123], issue #123, etc.
            if echo "$SECTION_CONTENT" | grep -qE "(^|[^0-9])#$issue([^0-9]|$)"; then
                ISSUES_TO_REMOVE+=("Issue #$issue found in section '$section'")
            fi
        fi
    done
done

# Report results
if [ ${#ISSUES_TO_REMOVE[@]} -gt 0 ]; then
    echo "❌ ROADMAP.md is out of sync with closed issues:"
    echo ""
    for issue_info in "${ISSUES_TO_REMOVE[@]}"; do
        echo "  - $issue_info"
    done
    echo ""
    echo "Action required:"
    echo "  1. Review each issue above"
    echo "  2. Remove from active sections in $ROADMAP_FILE"
    echo "  3. Either delete the reference or move to 'Completed' section"
    echo ""
    exit 1
else
    echo "✅ ROADMAP.md is synced with closed issues"
    echo "All $ISSUE_COUNT closed issue(s) have been removed from active sections"
    exit 0
fi
