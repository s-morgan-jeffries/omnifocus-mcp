#!/bin/bash
# Check if CHANGELOG.md date has been updated from "TBD" before final release tag
# Addresses issue #166

# This script should be run ONLY for final release tags (not RC tags)
# It verifies that CHANGELOG.md has an actual date instead of "TBD"

# Get tag name from argument (if provided by pre-tag hook)
TAG_NAME="${1:-}"

echo "📅 Checking CHANGELOG.md date..."

# Get current version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

if [ -z "$VERSION" ]; then
    echo "❌ Could not read version from pyproject.toml"
    exit 1
fi

echo "   Current version: $VERSION"

# Check if CHANGELOG.md exists
if [ ! -f "CHANGELOG.md" ]; then
    echo "❌ CHANGELOG.md not found"
    exit 1
fi

# Extract the date for the current version from CHANGELOG.md
# Format: ## [X.Y.Z] - DATE or ## [X.Y.Z] - TBD
CHANGELOG_LINE=$(grep -E "^## \[$VERSION\]" CHANGELOG.md | head -1)

if [ -z "$CHANGELOG_LINE" ]; then
    echo "❌ Version $VERSION not found in CHANGELOG.md"
    echo "   Expected format: ## [$VERSION] - DATE"
    exit 1
fi

# Extract the date part
CHANGELOG_DATE=$(echo "$CHANGELOG_LINE" | sed -E 's/^## \[[^]]+\] - (.+)$/\1/')

echo "   CHANGELOG date: $CHANGELOG_DATE"
echo ""

# Check if date is "TBD"
if [ "$CHANGELOG_DATE" = "TBD" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ CHANGELOG.md still has 'TBD' date!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Version: $VERSION"
    echo "   Current line: $CHANGELOG_LINE"
    echo ""
    echo "📝 Action required:"
    echo "   1. Update CHANGELOG.md to replace 'TBD' with actual release date"
    echo "   2. Format: ## [$VERSION] - YYYY-MM-DD"
    echo "   3. Commit the date update to main"
    echo "   4. THEN create the release tag"
    echo ""
    echo "💡 Correct workflow (issue #166):"
    echo "   ✅ Create RC tag with CHANGELOG='TBD'"
    echo "   ✅ Validate RC"
    echo "   ✅ Merge release branch to main"
    echo "   ✅ Update CHANGELOG date (THIS STEP)"
    echo "   ✅ Commit date update"
    echo "   ⚠️  THEN create final release tag"
    echo ""
    echo "   This ensures the release tag includes the correct date."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    exit 1
fi

# If we get here, date is set to something other than "TBD"
# Optionally validate date format (YYYY-MM-DD)
if echo "$CHANGELOG_DATE" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
    DATE_FORMAT="✅ Valid format (YYYY-MM-DD)"
else
    DATE_FORMAT="⚠️  Non-standard format (expected YYYY-MM-DD)"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CHANGELOG.md date is set!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Version: $VERSION"
echo "   Date: $CHANGELOG_DATE"
echo "   $DATE_FORMAT"
echo ""
exit 0
