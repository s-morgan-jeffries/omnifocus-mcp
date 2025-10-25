#!/bin/bash
# Migrates MISTAKES.md entries to GitHub Issues
#
# Usage:
#   ./scripts/migrate_mistakes_to_issues.sh          # Dry run (shows what would be created)
#   ./scripts/migrate_mistakes_to_issues.sh execute  # Actually create issues

set -e

MISTAKES_FILE=".claude/mistakes/MISTAKES.md"
MODE="${1:-dry-run}"

if [ "$MODE" = "execute" ]; then
    echo "🚀 EXECUTING migration (will create GitHub Issues)"
    DRY_RUN=false
else
    echo "🔍 DRY RUN mode (use './scripts/migrate_mistakes_to_issues.sh execute' to actually create issues)"
    DRY_RUN=true
fi

echo ""
echo "Parsing $MISTAKES_FILE..."
echo ""

# Counter for created issues
ISSUE_COUNT=0

# Temporary storage for current mistake being parsed
CURRENT_MISTAKE=""
CURRENT_TITLE=""
CURRENT_STATUS=""
CURRENT_CATEGORY=""
CURRENT_SEVERITY=""
CURRENT_BODY=""
IN_MISTAKE=false

# Process line by line
while IFS= read -r line; do
    # Detect start of a mistake entry
    if [[ "$line" =~ ^\#\#\ \[MISTAKE-([0-9]+)\]\ (.+)\ \(Date:\ ([0-9-]+)\) ]]; then
        # If we were processing a previous mistake, create its issue
        if [ "$IN_MISTAKE" = true ] && [ -n "$CURRENT_TITLE" ]; then
            # Create the issue
            LABELS="ai-process"
            [ -n "$CURRENT_CATEGORY" ] && LABELS="$LABELS,$CURRENT_CATEGORY"
            [ -n "$CURRENT_SEVERITY" ] && LABELS="$LABELS,$CURRENT_SEVERITY"

            echo "---"
            echo "Would create issue: $CURRENT_TITLE"
            echo "Labels: $LABELS"
            echo "Status: $CURRENT_STATUS ($([ "$CURRENT_STATUS" = "resolved" ] || [ "$CURRENT_STATUS" = "archived" ] && echo "will be CLOSED" || echo "will be OPEN"))"

            if [ "$DRY_RUN" = false ]; then
                # Write body to temp file for proper formatting
                TEMP_BODY=$(mktemp)
                printf "%b" "$CURRENT_BODY" > "$TEMP_BODY"

                # Create issue and capture URL
                ISSUE_URL=$(gh issue create \
                    --title "$CURRENT_TITLE" \
                    --body-file "$TEMP_BODY" \
                    --label "$LABELS")

                # Clean up temp file
                rm "$TEMP_BODY"

                # Extract issue number from URL
                ISSUE_NUM=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')

                echo "✅ Created issue #$ISSUE_NUM: $ISSUE_URL"

                # Close if status was resolved/archived
                if [ "$CURRENT_STATUS" = "resolved" ] || [ "$CURRENT_STATUS" = "archived" ]; then
                    gh issue close "$ISSUE_NUM"
                    echo "  ↳ Closed (original status: $CURRENT_STATUS)"
                fi

                ((ISSUE_COUNT++))
            fi
            echo ""
        fi

        # Start new mistake
        MISTAKE_NUM="${BASH_REMATCH[1]}"
        TITLE_PART="${BASH_REMATCH[2]}"
        DISCOVERY_DATE="${BASH_REMATCH[3]}"

        CURRENT_MISTAKE="MISTAKE-$MISTAKE_NUM"
        CURRENT_TITLE="$CURRENT_MISTAKE: $TITLE_PART"
        CURRENT_STATUS=""
        CURRENT_CATEGORY=""
        CURRENT_SEVERITY=""
        CURRENT_BODY="# $CURRENT_TITLE\n\n**Original ID:** $CURRENT_MISTAKE\n**Discovery Date:** $DISCOVERY_DATE\n"
        IN_MISTAKE=true

    elif [ "$IN_MISTAKE" = true ]; then
        # Extract metadata fields
        if [[ "$line" =~ ^\*\*Status:\*\*\ (.+)$ ]]; then
            CURRENT_STATUS="${BASH_REMATCH[1]}"
            CURRENT_BODY+="\n*This issue was migrated from \`.claude/mistakes/MISTAKES.md\` on $(date +%Y-%m-%d). Original status was \"$CURRENT_STATUS\" - now tracked via GitHub issue state (open = monitoring/working on it, closed = resolved).*\n"

        elif [[ "$line" =~ ^\*\*Category:\*\*\ (.+)$ ]]; then
            CURRENT_CATEGORY="${BASH_REMATCH[1]}"
            CURRENT_BODY+="\n**Category:** $CURRENT_CATEGORY\n"

        elif [[ "$line" =~ ^\*\*Severity:\*\*\ (.+)$ ]]; then
            CURRENT_SEVERITY="${BASH_REMATCH[1]}"
            CURRENT_BODY+="\n**Severity:** $CURRENT_SEVERITY\n"

        elif [[ "$line" =~ ^\*\*Discovery\ Date:\*\*|^\*\*Introduced\ In:\*\*|^\*\*Recurrence\ Count:\*\*|^\*\*Last\ Recurrence:\*\* ]]; then
            # Skip these - already captured or not needed
            continue

        elif [[ "$line" =~ ^\*\*Verification\ Deadline:\*\* ]]; then
            # Skip verification deadline (we're not using it)
            continue

        elif [[ "$line" =~ ^\*\*What\ Happened:\*\* ]]; then
            CURRENT_BODY+="\n## What Happened\n"

        elif [[ "$line" =~ ^\*\*Context:\*\* ]]; then
            CURRENT_BODY+="\n## Context\n"

        elif [[ "$line" =~ ^\*\*Impact:\*\* ]]; then
            CURRENT_BODY+="\n## Impact\n"

        elif [[ "$line" =~ ^\*\*Root\ Cause:\*\* ]]; then
            CURRENT_BODY+="\n## Root Cause\n"

        elif [[ "$line" =~ ^\*\*Fix:\*\* ]]; then
            CURRENT_BODY+="\n## Prevention Measures\n\n### Immediate Fix\n"

        elif [[ "$line" =~ ^\*\*Prevention:\*\* ]]; then
            CURRENT_BODY+="\n### Long-term Prevention\n"

        elif [[ "$line" =~ ^\*\*Related\ Mistakes:\*\* ]]; then
            CURRENT_BODY+="\n## Related Issues\n"

        elif [[ "$line" =~ ^\*\*Effectiveness\ Score:\*\* ]]; then
            # Skip effectiveness score
            continue

        elif [[ "$line" =~ ^---$ ]]; then
            # End of mistake entry marker
            continue

        else
            # Regular content line - add to body
            CURRENT_BODY+="$line\n"
        fi
    fi
done < "$MISTAKES_FILE"

# Don't forget the last mistake
if [ "$IN_MISTAKE" = true ] && [ -n "$CURRENT_TITLE" ]; then
    LABELS="ai-process"
    [ -n "$CURRENT_CATEGORY" ] && LABELS="$LABELS,$CURRENT_CATEGORY"
    [ -n "$CURRENT_SEVERITY" ] && LABELS="$LABELS,$CURRENT_SEVERITY"

    echo "---"
    echo "Would create issue: $CURRENT_TITLE"
    echo "Labels: $LABELS"
    echo "Status: $CURRENT_STATUS ($([ "$CURRENT_STATUS" = "resolved" ] || [ "$CURRENT_STATUS" = "archived" ] && echo "will be CLOSED" || echo "will be OPEN"))"

    if [ "$DRY_RUN" = false ]; then
        TEMP_BODY=$(mktemp)
        printf "%b" "$CURRENT_BODY" > "$TEMP_BODY"

        ISSUE_URL=$(gh issue create \
            --title "$CURRENT_TITLE" \
            --body-file "$TEMP_BODY" \
            --label "$LABELS")

        rm "$TEMP_BODY"

        ISSUE_NUM=$(echo "$ISSUE_URL" | grep -oE '[0-9]+$')

        echo "✅ Created issue #$ISSUE_NUM: $ISSUE_URL"

        if [ "$CURRENT_STATUS" = "resolved" ] || [ "$CURRENT_STATUS" = "archived" ]; then
            gh issue close "$ISSUE_NUM"
            echo "  ↳ Closed (original status: $CURRENT_STATUS)"
        fi

        ((ISSUE_COUNT++))
    fi
    echo ""
fi

echo "================================"
if [ "$DRY_RUN" = true ]; then
    echo "✅ Dry run complete - no issues created"
    echo "Run './scripts/migrate_mistakes_to_issues.sh execute' to create issues"
else
    echo "✅ Migration complete!"
    echo "Created $ISSUE_COUNT issues"
    echo ""
    echo "View issues: gh issue list --label ai-process"
fi
