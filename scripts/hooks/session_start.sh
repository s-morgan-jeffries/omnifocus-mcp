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

# Add milestone information (#45)
if command -v gh &> /dev/null; then
    # Get current version from pyproject.toml
    CURRENT_VERSION=$(grep '^version = ' pyproject.toml 2>/dev/null | cut -d'"' -f2)

    if [ -n "$CURRENT_VERSION" ]; then
        # Calculate next patch version for current milestone
        CURRENT_PATCH=$(echo "$CURRENT_VERSION" | sed 's/.*\.\([0-9]*\)$/\1/')
        NEXT_PATCH=$((CURRENT_PATCH + 1))
        CURRENT_MILESTONE="v0.6.$NEXT_PATCH"

        # Check if milestone exists
        MILESTONE_EXISTS=$(gh api repos/:owner/:repo/milestones --jq ".[] | select(.title == \"$CURRENT_MILESTONE\") | .number" 2>/dev/null)

        if [ -n "$MILESTONE_EXISTS" ]; then
            # Get open issues count
            MILESTONE_OPEN=$(gh issue list --milestone "$CURRENT_MILESTONE" --state open --json number -q 'length' 2>/dev/null || echo "0")

            CONTEXT+="**📍 Active Milestone:** $CURRENT_MILESTONE ($MILESTONE_OPEN open issues)\n"

            # List open issues in milestone
            if [ "$MILESTONE_OPEN" != "0" ]; then
                MILESTONE_ISSUES=$(gh issue list --milestone "$CURRENT_MILESTONE" --state open --json number,title --jq '.[] | "  - #\(.number): \(.title)"' 2>/dev/null)
                if [ -n "$MILESTONE_ISSUES" ]; then
                    CONTEXT+="\n$MILESTONE_ISSUES\n"
                fi
            fi
            CONTEXT+="\n"
        else
            CONTEXT+="**⚠️  No active milestone found!**\n"
            CONTEXT+="Expected: $CURRENT_MILESTONE (based on current version v$CURRENT_VERSION)\n"
            CONTEXT+="Action: Create milestone or assign issues to existing milestone\n\n"
        fi
    fi

    # Total open issues
    OPEN_ISSUES=$(gh issue list --state open --json number -q 'length' 2>/dev/null || echo "unknown")
    CONTEXT+="**Total open issues:** $OPEN_ISSUES\n\n"
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
    echo 'export PYTHONPATH="$CLAUDE_PROJECT_DIR/src:$PYTHONPATH"' >> "$CLAUDE_ENV_FILE"
fi

exit 0
