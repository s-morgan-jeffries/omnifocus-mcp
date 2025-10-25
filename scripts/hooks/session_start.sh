#!/bin/bash
# SessionStart hook
# Loads project context and warns about potential issues
#
# Related issues: #43
# Priority: MEDIUM - Provides situational awareness

echo "Loading OmniFocus MCP project context..." >&2

# Prepare context to inject into session
CONTEXT="# Current Project State\n\n"

# Add git status
GIT_STATUS=$(git status --short 2>/dev/null)
if [ -n "$GIT_STATUS" ]; then
    CONTEXT+="## Git Status\n\`\`\`\n$GIT_STATUS\n\`\`\`\n\n"
fi

# Add current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
CONTEXT+="**Current branch:** $BRANCH\n\n"

# Warn if on main
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    CONTEXT+="⚠️  **WARNING:** You are on the $BRANCH branch. Create a feature branch before making changes:\n"
    CONTEXT+="\`\`\`bash\ngit checkout -b feature/description\n\`\`\`\n\n"
fi

# Add open issues count
if command -v gh &> /dev/null; then
    OPEN_ISSUES=$(gh issue list --state open --json number -q 'length' 2>/dev/null || echo "unknown")
    CONTEXT+="**Open issues:** $OPEN_ISSUES\n\n"

    # Add current milestone (v0.6.2)
    CURRENT_MILESTONE="v0.6.2"
    MILESTONE_OPEN=$(gh issue list --milestone "$CURRENT_MILESTONE" --state open --json number -q 'length' 2>/dev/null || echo "0")
    if [ "$MILESTONE_OPEN" != "0" ]; then
        CONTEXT+="**Current milestone:** $CURRENT_MILESTONE ($MILESTONE_OPEN open issues)\n\n"
    fi
fi

# Add recent commits
RECENT_COMMITS=$(git log --oneline -5 2>/dev/null)
if [ -n "$RECENT_COMMITS" ]; then
    CONTEXT+="## Recent Commits\n\`\`\`\n$RECENT_COMMITS\n\`\`\`\n\n"
fi

# Add workflow reminders
CONTEXT+="## Workflow Reminders\n"
CONTEXT+="- Create feature branch before starting work\n"
CONTEXT+="- Follow TDD: write tests first\n"
CONTEXT+="- Monitor CI after git push (automated via hooks)\n"
CONTEXT+="- Update ROADMAP.md when completing issues\n"
CONTEXT+="- Reference issue numbers in commits\n\n"

# Return context as JSON
cat <<EOF
{
  "additionalContext": $(echo -e "$CONTEXT" | jq -Rs .)
}
EOF

# Set environment variables for subsequent Bash tool calls
if [ -n "$CLAUDE_ENV_FILE" ]; then
    echo 'export OMNIFOCUS_TEST_MODE=true' >> "$CLAUDE_ENV_FILE"
    echo 'export PYTHONPATH="$CLAUDE_PROJECT_DIR/src:$PYTHONPATH"' >> "$CLAUDE_ENV_FILE"
fi

exit 0
