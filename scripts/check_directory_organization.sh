#!/bin/bash
# Check directory organization for cleanliness
# Returns 0 if organization is good, 1 if issues found

echo "Checking directory organization..."

ISSUES_FOUND=0

# Check 1: Look for orphaned files in .claude/
echo "1. Checking .claude/ directory..."
EXPECTED_CLAUDE_FILES=(
    ".claude/CLAUDE.md"
    ".claude/CLAUDE-redesign-phase.md"
    ".claude/settings.json"
    ".claude/mistakes/README.md"
    ".claude/mistakes/MISTAKES.md"
)

ORPHANED_CLAUDE=()
while IFS= read -r -d '' file; do
    # Skip directories and expected files
    IS_EXPECTED=false
    for expected in "${EXPECTED_CLAUDE_FILES[@]}"; do
        if [[ "$file" == "$expected"* ]]; then
            IS_EXPECTED=true
            break
        fi
    done

    if [ "$IS_EXPECTED" = false ]; then
        # Check if it's in mistakes/ subdirectory (allowed)
        if [[ ! "$file" =~ ^\.claude/mistakes/ ]]; then
            ORPHANED_CLAUDE+=("$file")
        fi
    fi
done < <(find .claude -type f -print0 2>/dev/null)

if [ ${#ORPHANED_CLAUDE[@]} -gt 0 ]; then
    echo "   ⚠️  Found unexpected files in .claude/:"
    for file in "${ORPHANED_CLAUDE[@]}"; do
        echo "      - $file"
    done
else
    echo "   ✅ .claude/ directory is organized"
fi

# Check 2: Look for orphaned scripts
echo "2. Checking scripts/ directory..."
EXPECTED_SCRIPT_DIRS=(
    "scripts/archive"
    "scripts/git-hooks"
    "scripts/hooks"
)

# Look for .sh files not in expected locations
ORPHANED_SCRIPTS=()
while IFS= read -r file; do
    # Skip files in expected directories
    IS_EXPECTED=false
    for dir in "${EXPECTED_SCRIPT_DIRS[@]}"; do
        if [[ "$file" == "$dir"* ]]; then
            IS_EXPECTED=true
            break
        fi
    done

    # Skip top-level scripts/ *.sh files (these are fine)
    if [[ "$file" =~ ^scripts/[^/]+\.sh$ ]]; then
        IS_EXPECTED=true
    fi

    if [ "$IS_EXPECTED" = false ]; then
        # Check if it's in an unexpected subdirectory
        if [[ "$file" =~ ^scripts/[^/]+/[^/]+/ ]]; then
            ORPHANED_SCRIPTS+=("$file")
        fi
    fi
done < <(find scripts -name "*.sh" -type f 2>/dev/null)

if [ ${#ORPHANED_SCRIPTS[@]} -gt 0 ]; then
    echo "   ⚠️  Found scripts in unexpected locations:"
    for file in "${ORPHANED_SCRIPTS[@]}"; do
        echo "      - $file"
    done
else
    echo "   ✅ scripts/ directory is organized"
fi

# Check 3: Look for orphaned documentation
echo "3. Checking docs/ directory..."
EXPECTED_DOC_DIRS=(
    "docs/guides"
    "docs/reference"
    "docs/project"
)

# Check for markdown files not in expected subdirectories
ORPHANED_DOCS=()
while IFS= read -r file; do
    # Skip files in expected directories
    IS_EXPECTED=false
    for dir in "${EXPECTED_DOC_DIRS[@]}"; do
        if [[ "$file" == "$dir"* ]]; then
            IS_EXPECTED=true
            break
        fi
    done

    if [ "$IS_EXPECTED" = false ]; then
        # Top-level docs/*.md files should be investigated
        if [[ "$file" =~ ^docs/[^/]+\.md$ ]]; then
            ORPHANED_DOCS+=("$file")
        fi
    fi
done < <(find docs -name "*.md" -type f 2>/dev/null)

if [ ${#ORPHANED_DOCS[@]} -gt 0 ]; then
    echo "   ⚠️  Found docs not in standard subdirectories:"
    for file in "${ORPHANED_DOCS[@]}"; do
        echo "      - $file (should be in guides/, reference/, or project/)"
    done
else
    echo "   ✅ docs/ directory is organized"
fi

# Check 4: Look for empty directories
echo "4. Checking for empty directories..."
EMPTY_DIRS=()
while IFS= read -r dir; do
    if [ -z "$(ls -A "$dir" 2>/dev/null)" ]; then
        EMPTY_DIRS+=("$dir")
    fi
done < <(find . -type d -not -path "./.git/*" -not -path "./.*" 2>/dev/null)

if [ ${#EMPTY_DIRS[@]} -gt 0 ]; then
    echo "   ⚠️  Found empty directories:"
    for dir in "${EMPTY_DIRS[@]}"; do
        echo "      - $dir"
    done
else
    echo "   ✅ No empty directories found"
fi

# Check 5: Look for test files outside tests/
echo "5. Checking for misplaced test files..."
MISPLACED_TESTS=$(find . -name "test_*.py" -not -path "./tests/*" -not -path "./.git/*" -not -path "./.*" 2>/dev/null || true)
if [ -n "$MISPLACED_TESTS" ]; then
    echo "   ⚠️  Found test files outside tests/ directory:"
    echo "$MISPLACED_TESTS" | sed 's/^/      /'
else
    echo "   ✅ All test files in tests/ directory"
fi

echo ""
if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ Directory organization check passed"
    echo "   (Warnings above are informational, not blocking)"
    exit 0
else
    echo "❌ Directory organization has issues"
    echo "   Consider cleaning up before release"
    exit 1
fi
