#!/bin/bash
# Check documentation completeness for a release
# Takes version as argument (e.g., v0.6.3)
# Returns 0 if documentation is complete, 1 if issues found

VERSION="$1"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v0.6.3"
    exit 1
fi

echo "Checking documentation completeness for $VERSION..."

ISSUES_FOUND=0

# Check 1: CHANGELOG.md has entry for this version
echo "1. Checking CHANGELOG.md for $VERSION entry..."
if grep -q "## \[${VERSION#v}\]" CHANGELOG.md; then
    echo "   ✅ CHANGELOG.md has entry for $VERSION"
else
    echo "   ❌ CHANGELOG.md missing entry for $VERSION"
    ISSUES_FOUND=1
fi

# Check 2: CLAUDE.md has current version updated
echo "2. Checking .claude/CLAUDE.md version..."
if grep -q "Current Version.*${VERSION#v}" .claude/CLAUDE.md; then
    echo "   ✅ CLAUDE.md current version is $VERSION"
else
    echo "   ❌ CLAUDE.md current version not updated to $VERSION"
    ISSUES_FOUND=1
fi

# Check 3: README.md has version updated comprehensively
echo "3. Checking README.md version references..."
README_ISSUES=0

# Check 3a: Installation example should reference current version
if grep -q "git checkout ${VERSION}" README.md; then
    echo "   ✅ Installation example references $VERSION"
else
    echo "   ❌ Installation example should reference '$VERSION' (currently references old version)"
    README_ISSUES=1
fi

# Check 3b: "Key Changes" section should mention current version
if grep -q "Key Changes.*${VERSION}" README.md; then
    echo "   ✅ 'Key Changes' section mentions $VERSION"
else
    echo "   ❌ 'Key Changes' section should include $VERSION"
    README_ISSUES=1
fi

# Check 3c: API version header should reference current version
if grep -q "v${VERSION#v} API" README.md; then
    echo "   ✅ API version header mentions $VERSION"
else
    echo "   ⚠️  API version header may need update to $VERSION"
fi

if [ $README_ISSUES -gt 0 ]; then
    ISSUES_FOUND=1
fi

# Check 4: Check for breaking changes requiring migration guide
echo "4. Checking for breaking changes..."
CHANGELOG_ENTRY=$(sed -n "/## \[${VERSION#v}\]/,/## \[/p" CHANGELOG.md)

if echo "$CHANGELOG_ENTRY" | grep -qi "breaking"; then
    echo "   ⚠️  CHANGELOG mentions breaking changes"
    # Check if migration guide exists
    MIGRATION_FILE="docs/guides/MIGRATION_${VERSION}.md"
    if [ -f "$MIGRATION_FILE" ]; then
        echo "      ✅ Migration guide exists: $MIGRATION_FILE"
    else
        echo "      ❌ Migration guide missing: $MIGRATION_FILE"
        echo "      Breaking changes require a migration guide"
        ISSUES_FOUND=1
    fi
else
    echo "   ✅ No breaking changes detected"
fi

# Check 5: Verify key documentation files exist
echo "5. Checking for key documentation files..."
KEY_DOCS=(
    "docs/guides/TESTING.md"
    "docs/guides/CONTRIBUTING.md"
    "docs/guides/INTEGRATION_TESTING.md"
    "docs/reference/ARCHITECTURE.md"
    "docs/reference/CODE_QUALITY.md"
    "docs/reference/APPLESCRIPT_GOTCHAS.md"
    "docs/project/ROADMAP.md"
)

MISSING_DOCS=()
for doc in "${KEY_DOCS[@]}"; do
    if [ ! -f "$doc" ]; then
        MISSING_DOCS+=("$doc")
    fi
done

if [ ${#MISSING_DOCS[@]} -gt 0 ]; then
    echo "   ❌ Missing key documentation files:"
    for doc in "${MISSING_DOCS[@]}"; do
        echo "      - $doc"
    done
    ISSUES_FOUND=1
else
    echo "   ✅ All key documentation files exist"
fi

echo ""
if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ Documentation check passed"
    exit 0
else
    echo "❌ Documentation check failed"
    echo "   Fix the issues above before releasing"
    exit 1
fi
