#!/bin/bash
# Automatically sync version across all files when pyproject.toml changes
#
# This script is called by git hooks to ensure version consistency.
# It updates:
# - .claude/CLAUDE.md
# - CHANGELOG.md (verifies entry exists)
# - README.md

set -e

# Get version from pyproject.toml (authoritative source)
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

if [ -z "$VERSION" ]; then
    echo "❌ Could not extract version from pyproject.toml"
    exit 1
fi

echo "🔄 Syncing version: $VERSION"

# Update .claude/CLAUDE.md
if [ -f ".claude/CLAUDE.md" ]; then
    # Update "Current Version:" line
    if grep -q "^**Current Version:**" .claude/CLAUDE.md; then
        # Extract current version description (e.g., "v0.6.2 (Claude Code Hooks)")
        CURRENT_DESC=$(grep "^**Current Version:**" .claude/CLAUDE.md | sed 's/^**Current Version:** v[0-9.]*\(.*\)/\1/')

        # Update with new version, keeping description
        sed -i.bak "s/^**Current Version:**.*/**Current Version:** v${VERSION}${CURRENT_DESC}/" .claude/CLAUDE.md
        rm .claude/CLAUDE.md.bak
        echo "  ✅ Updated .claude/CLAUDE.md"
    else
        echo "  ⚠️  Warning: Could not find 'Current Version' in .claude/CLAUDE.md"
    fi
fi

# Verify CHANGELOG.md has entry for this version
if [ -f "CHANGELOG.md" ]; then
    if grep -q "^## \[${VERSION}\]" CHANGELOG.md || grep -q "^## \[v${VERSION}\]" CHANGELOG.md; then
        echo "  ✅ CHANGELOG.md has entry for v${VERSION}"
    else
        echo "  ⚠️  Warning: CHANGELOG.md missing entry for v${VERSION}"
        echo "     Add a changelog entry before committing"
    fi
fi

# Update README.md version references
if [ -f "README.md" ]; then
    # Update "This server provides ... (vX.Y.Z API)"
    if grep -q "(v[0-9.]* API)" README.md; then
        sed -i.bak "s/(v[0-9.]* API)/(v${VERSION} API)/" README.md
        rm README.md.bak
        echo "  ✅ Updated README.md API version"
    fi

    # Update installation example (git checkout vX.Y.Z)
    if grep -q "git checkout v[0-9][0-9.]*  # Or latest version" README.md; then
        sed -i.bak "s/git checkout v[0-9][0-9.]*  # Or latest version/git checkout v${VERSION}  # Or latest version/" README.md
        rm README.md.bak
        echo "  ✅ Updated README.md installation example"
    fi
fi

echo "✅ Version sync complete: v${VERSION}"
