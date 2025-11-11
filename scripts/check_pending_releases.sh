#!/bin/bash
# Check for pending releases (RC tags without corresponding final tags)
#
# Purpose: Detect incomplete releases where RC tag was created but final release forgotten
# Usage: ./scripts/check_pending_releases.sh
# Exit codes: 0=no pending releases, 1=pending release(s) found

set -e

echo "Checking for pending releases..."
echo ""

PENDING_FOUND=0

# Get all RC tags
RC_TAGS=$(git for-each-ref --sort=-version:refname --format='%(refname:short)' refs/tags | grep -E "v[0-9]+\.[0-9]+\.[0-9]+-rc[0-9]+" || true)

if [ -z "$RC_TAGS" ]; then
    echo "✅ No RC tags found"
    exit 0
fi

# Check each RC tag for corresponding final tag
while IFS= read -r rc_tag; do
    # Extract version from RC tag (e.g., v0.6.7-rc1 -> v0.6.7)
    version=$(echo "$rc_tag" | sed 's/-rc[0-9]*$//')

    # Check if final tag exists
    if git rev-parse "$version" >/dev/null 2>&1; then
        echo "✅ $rc_tag → $version (released)"
    else
        echo "❌ $rc_tag → $version (PENDING - final tag missing)"
        PENDING_FOUND=1

        # Get RC tag date
        rc_date=$(git log -1 --format='%ci' "$rc_tag" | cut -d' ' -f1)
        echo "   RC created: $rc_date"
        echo "   Action: Complete release or document as skipped in CHANGELOG"
        echo ""
    fi
done <<< "$RC_TAGS"

echo ""

if [ $PENDING_FOUND -eq 1 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  PENDING RELEASES DETECTED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "One or more RC tags exist without corresponding final releases."
    echo ""
    echo "Options:"
    echo "  1. Complete the release: ./scripts/create_tag.sh <version>"
    echo "  2. Skip the release: Document in CHANGELOG as skipped"
    echo "  3. Delete the RC tag: git tag -d <rc-tag> && git push origin :refs/tags/<rc-tag>"
    echo ""
    exit 1
else
    echo "✅ All RC tags have corresponding final releases"
    exit 0
fi
