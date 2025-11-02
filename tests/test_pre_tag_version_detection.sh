#!/bin/bash
# Test script for pre-tag hook version detection
# Tests the version type detection logic without running full hook

set -e

echo "Testing version detection logic..."
echo ""

# Test function that mimics the hook's version detection
test_version_detection() {
    local TAG_NAME="$1"
    local EXPECTED_TYPE="$2"

    if [[ "$TAG_NAME" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
        MAJOR="${BASH_REMATCH[1]}"
        MINOR="${BASH_REMATCH[2]}"
        PATCH="${BASH_REMATCH[3]}"

        if [ "$PATCH" != "0" ]; then
            RELEASE_TYPE="patch"
        elif [ "$MINOR" != "0" ]; then
            RELEASE_TYPE="minor"
        else
            RELEASE_TYPE="major"
        fi
    else
        RELEASE_TYPE="patch"
    fi

    if [ "$RELEASE_TYPE" = "$EXPECTED_TYPE" ]; then
        echo "✅ $TAG_NAME → $RELEASE_TYPE (expected: $EXPECTED_TYPE)"
    else
        echo "❌ $TAG_NAME → $RELEASE_TYPE (expected: $EXPECTED_TYPE)"
        exit 1
    fi
}

# Test cases
echo "Testing patch releases (v0.6.x):"
test_version_detection "v0.6.1" "patch"
test_version_detection "v0.6.7" "patch"
test_version_detection "v0.6.99" "patch"
test_version_detection "v0.6.1-rc1" "patch"
test_version_detection "v0.6.7-rc2" "patch"

echo ""
echo "Testing minor releases (v0.x.0):"
test_version_detection "v0.7.0" "minor"
test_version_detection "v0.8.0" "minor"
test_version_detection "v0.99.0" "minor"
test_version_detection "v0.7.0-rc1" "minor"
test_version_detection "v0.8.0-rc2" "minor"

echo ""
echo "Testing major releases (vX.0.0):"
test_version_detection "v1.0.0" "major"
test_version_detection "v2.0.0" "major"
test_version_detection "v1.0.0-rc1" "major"
test_version_detection "v2.0.0-rc2" "major"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All version detection tests passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
