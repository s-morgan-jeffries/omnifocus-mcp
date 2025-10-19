#!/bin/bash
# Install optional git hooks for mistake tracking

echo "📦 Installing git hooks for mistake tracking..."
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
echo "To uninstall: rm .git/hooks/commit-msg"
