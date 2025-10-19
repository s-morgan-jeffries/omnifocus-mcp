#!/bin/bash
# Check if version numbers are synchronized across all files
# Addresses MISTAKE-003 root cause

echo "🔢 Checking version synchronization..."

# Get authoritative version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

if [ -z "$VERSION" ]; then
    echo "❌ Could not read version from pyproject.toml"
    exit 1
fi

echo "   Authoritative version (pyproject.toml): $VERSION"
echo ""

MISMATCHES=0
MATCHED=0

# Check .claude/CLAUDE.md
FILE=".claude/CLAUDE.md"
PATTERN="Current Version.*v?$VERSION"
if [ ! -f "$FILE" ]; then
    echo "⚠️  $FILE not found (skipping)"
else
    if grep -qE "$PATTERN" "$FILE"; then
        echo "✅ $FILE: v$VERSION found"
        ((MATCHED++))
    else
        echo "❌ $FILE: v$VERSION NOT found"
        echo "   Expected pattern: $PATTERN"
        ((MISMATCHES++))
    fi
fi

# Check CHANGELOG.md
FILE="CHANGELOG.md"
PATTERN="## \[$VERSION\]"
if [ ! -f "$FILE" ]; then
    echo "⚠️  $FILE not found (skipping)"
else
    if grep -qE "$PATTERN" "$FILE"; then
        echo "✅ $FILE: v$VERSION found"
        ((MATCHED++))
    else
        echo "❌ $FILE: v$VERSION NOT found"
        echo "   Expected pattern: $PATTERN"
        ((MISMATCHES++))
    fi
fi

# Check README.md
FILE="README.md"
PATTERN="v$VERSION"
if [ ! -f "$FILE" ]; then
    echo "⚠️  $FILE not found (skipping)"
else
    if grep -qE "$PATTERN" "$FILE"; then
        echo "✅ $FILE: v$VERSION found"
        ((MATCHED++))
    else
        echo "❌ $FILE: v$VERSION NOT found"
        echo "   Expected pattern: $PATTERN"
        ((MISMATCHES++))
    fi
fi

echo ""

if [ $MISMATCHES -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ All version references are synchronized!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Version: $VERSION"
    echo "   Files checked: $MATCHED"
    echo ""
    exit 0
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Version mismatch detected!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Authoritative: $VERSION (pyproject.toml)"
    echo "   Mismatches: $MISMATCHES file(s)"
    echo ""
    echo "📝 Action required:"
    echo "   Follow the 'Making a Release' workflow in docs/guides/CONTRIBUTING.md"
    echo ""
    echo "   Quick fix checklist:"
    echo "   1. ✅ pyproject.toml version = \"$VERSION\""
    echo "   2. Update .claude/CLAUDE.md 'Current Version: v$VERSION'"
    echo "   3. Add/update CHANGELOG.md entry '## [$VERSION]'"
    echo "   4. Update README.md if version appears in feature descriptions"
    echo ""
    echo "💡 Prevention (MISTAKE-003):"
    echo "   - pyproject.toml is authoritative source"
    echo "   - Run this script after version bumps"
    echo "   - Consider adding to pre-commit hook"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    exit 1
fi
