#!/bin/bash
# Install optional git hooks for mistake tracking

echo "📦 Installing git hooks for mistake tracking..."
echo ""

# Install pre-commit hook
if [ -f ".git/hooks/pre-commit" ]; then
    echo "⚠️  .git/hooks/pre-commit already exists"
    echo "   Backing up to .git/hooks/pre-commit.backup"
    mv .git/hooks/pre-commit .git/hooks/pre-commit.backup
fi

cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Installed pre-commit hook"
echo "   - Detects missing tests (missing-tests)"
echo "   - Detects missing server exposure (missing-exposure)"
echo "   - Detects version sync issues (missing-docs)"
echo "   - Detects missing migration guides (missing-docs)"
echo "   - Reminds to check complexity"
echo ""

# Install commit-msg hook
if [ -f ".git/hooks/commit-msg" ]; then
    echo "⚠️  .git/hooks/commit-msg already exists"
    echo "   Backing up to .git/hooks/commit-msg.backup"
    mv .git/hooks/commit-msg .git/hooks/commit-msg.backup
fi

cp scripts/git-hooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg

echo "✅ Installed commit-msg hook"
echo "   - Validates 'Resolves: MISTAKE-XXX' format"
echo "   - Ensures referenced mistake exists in MISTAKES.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Git hooks installed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To uninstall:"
echo "  rm .git/hooks/pre-commit .git/hooks/commit-msg"
