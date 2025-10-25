# Claude Code Hooks: Deep Dive

**Purpose:** This document explains how to use Claude Code hooks to create feedback loops that improve AI behavior over time by encoding process requirements as automated constraints.

**Last Updated:** 2025-10-25

---

## Philosophy: Simulating Learning Through Constraints

Unlike human developers, Claude Code cannot learn from past mistakes in the traditional sense. Each session starts fresh. However, we can approximate learning by:

1. **Documenting mistakes** (GitHub Issues with `ai-process` label)
2. **Designing prevention measures** (documented in issue bodies)
3. **Encoding prevention as hooks** (automated enforcement)
4. **Detecting recurrence** (CI checks via prevention scripts)

**Result:** Over time, the system accumulates constraints that prevent repeating past mistakes, creating a ratchet effect where the AI can only improve (or maintain) its behavior, never regress.

---

## Available Hook Events

| Event | When It Fires | Can Block Claude | Use For | Access To |
|-------|---------------|------------------|---------|-----------|
| **PreToolUse** | After parameters created, before tool execution | ✅ Yes | Prevent dangerous operations, enforce preconditions | Tool name, parameters |
| **PostToolUse** | After tool completes | ⚠️ Can inform Claude of issues | Validate results, trigger follow-up actions | Tool name, parameters, results |
| **UserPromptSubmit** | Before processing user prompt | ✅ Yes | Add context, block inappropriate requests | User prompt text |
| **Stop** | Before Claude finishes responding | ✅ Yes | Enforce checklist completion, validate work | Session transcript |
| **SubagentStop** | When subagent completes | ✅ Yes | Validate subagent work | Subagent transcript |
| **Notification** | When Claude needs permission/input | ⚠️ Informational | Log permission requests, audit decisions | Notification details |
| **SessionStart** | Session begins or resumes | ❌ No (can inject context) | Load project context, set environment | Session source (startup/resume/clear) |
| **SessionEnd** | Session terminates | ❌ No (cleanup only) | Backup transcripts, log session metrics | Session reason |
| **PreCompact** | Before context compaction | ⚠️ Can back up | Save transcript before memory loss | Current transcript |

---

## Blocking Mechanisms

### Exit Codes

```bash
exit 0  # Success - stdout shown in transcript (or added as context for UserPromptSubmit/SessionStart)
exit 2  # Blocking error - stderr fed to Claude automatically, Claude must address it
exit 1  # Non-blocking error - stderr shown to user, Claude continues
```

**Key insight:** Exit code 2 is your enforcement mechanism. Claude receives the error message and must resolve it before continuing.

### JSON Output Control

For sophisticated control, return JSON to stdout:

```json
{
  "continue": false,              // Stop processing
  "stopReason": "Tests failing",  // Why we're stopping
  "suppressOutput": false,        // Hide hook output from transcript
  "systemMessage": "Warning: ...", // Additional context for Claude
  "decision": "block",            // Event-specific blocking
  "reason": "Must fix tests",     // Explanation for blocking
  "additionalContext": "..."      // Extra info for Claude
}
```

**Event-specific blocking:**

| Event | Blocking JSON | Effect |
|-------|---------------|--------|
| **PreToolUse** | `{"permissionDecision": "deny", "permissionDecisionReason": "..."}` | Tool call rejected |
| **PostToolUse** | `{"decision": "block", "reason": "...", "additionalContext": "..."}` | Claude informed of failure |
| **UserPromptSubmit** | `{"decision": "block", "additionalContext": "..."}` | Prompt rejected, context shown |
| **Stop** | `{"decision": "block", "reason": "..."}` | Claude forced to continue, reason required |
| **SubagentStop** | `{"decision": "block", "reason": "..."}` | Subagent result rejected |

---

## Configuration Format

Hooks are defined in:
- `~/.claude/settings.json` (global, affects all projects)
- `.claude/settings.json` (project-specific, checked into git)
- `.claude/settings.local.json` (project-specific, gitignored for personal overrides)

**Recommended:** Use project-specific `.claude/settings.json` for team-wide enforcement.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",  // Or regex pattern, or "*" for all tools
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/hooks/pre_bash.sh \"$TOOL_INPUT\"",
            "timeout": 60
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/hooks/post_bash.sh \"$TOOL_INPUT\" \"$TOOL_RESPONSE\"",
            "timeout": 30
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/hooks/pre_stop.sh",
            "timeout": 120
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/hooks/session_start.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Note:** `PreToolUse` and `PostToolUse` require `matcher` field; other events don't use matchers.

---

## Hook Input Data

All hooks receive JSON via stdin:

```json
{
  "session_id": "unique-session-id",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/current/working/directory",
  "permission_mode": "ask|allow|deny",
  "hook_event_name": "PreToolUse",
  // Event-specific fields below...
}
```

**Event-specific fields:**

| Event | Additional Fields |
|-------|-------------------|
| **PreToolUse** | `tool_name`, `tool_input` (JSON object with tool parameters) |
| **PostToolUse** | `tool_name`, `tool_input`, `tool_response` (JSON object with results) |
| **UserPromptSubmit** | `prompt` (user's text) |
| **Stop** | `stop_hook_active` (boolean) |
| **SubagentStop** | `stop_hook_active` (boolean) |
| **SessionStart** | `source` ("startup" / "resume" / "clear" / "compact") |
| **SessionEnd** | `reason` (why session ended) |

**Parsing example:**

```bash
#!/bin/bash
# Read JSON from stdin
INPUT=$(cat)

# Extract fields using jq
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input')
CWD=$(echo "$INPUT" | jq -r '.cwd')

# Process...
```

---

## Enforcement Patterns for TDD and Process Compliance

### Pattern 1: Pre-Commit Test Validation (Stop Hook)

**Problem:** Claude commits code without running tests first.

**Solution:** Block Stop event until tests pass.

```bash
#!/bin/bash
# scripts/hooks/pre_stop.sh

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Uncommitted changes detected. Checking if tests have been run..." >&2

    # Check if tests were run in this session by examining transcript
    INPUT=$(cat)
    TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path')

    # Look for "make test" or "pytest" commands in transcript
    if ! grep -q "make test\|pytest" "$TRANSCRIPT_PATH"; then
        cat >&2 <<EOF
{
  "decision": "block",
  "reason": "Tests have not been run before committing. Please run 'make test' first."
}
EOF
        exit 2
    fi

    # Verify tests actually passed
    if grep -q "FAILED\|ERROR" "$TRANSCRIPT_PATH" | tail -20; then
        cat >&2 <<EOF
{
  "decision": "block",
  "reason": "Tests are failing. Please fix all test failures before committing."
}
EOF
        exit 2
    fi
fi

exit 0
```

### Pattern 2: Branch Validation (Pre-Commit via PreToolUse)

**Problem:** Claude works directly on main branch instead of feature branches (Issue #37).

**Solution:** Block git commits on main branch.

```bash
#!/bin/bash
# scripts/hooks/pre_bash.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

# Check if this is a git commit command
if echo "$COMMAND" | grep -qE "^git commit"; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

    # Block commits to main/master unless it's a hotfix
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        # Check if commit message contains "hotfix" or "emergency"
        if ! echo "$COMMAND" | grep -qiE "hotfix|emergency"; then
            cat >&2 <<EOF
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "Cannot commit directly to $CURRENT_BRANCH branch. Please create a feature branch first: git checkout -b feature/description"
}
EOF
            exit 2
        fi
    fi
fi

exit 0
```

### Pattern 3: Git Push Monitoring (PostToolUse)

**Problem:** Claude pushes code but doesn't monitor GitHub Actions (Issue #39).

**Solution:** After git push, wait for CI and report results.

```bash
#!/bin/bash
# scripts/hooks/post_bash.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0')

# Check if this was a successful git push
if echo "$COMMAND" | grep -qE "^git push" && [ "$EXIT_CODE" = "0" ]; then
    echo "Git push detected. Monitoring GitHub Actions..." >&2

    # Wait for CI to start
    sleep 5

    # Get latest run ID and watch it
    RUN_ID=$(gh run list --limit 1 --json databaseId -q '.[0].databaseId')

    if [ -n "$RUN_ID" ]; then
        # Watch the run with timeout
        if ! timeout 300 gh run watch "$RUN_ID" --exit-status 2>&1; then
            cat >&2 <<EOF
{
  "decision": "block",
  "reason": "GitHub Actions CI failed. Please review failures and fix before continuing.",
  "additionalContext": "View run: $(gh run view $RUN_ID --json url -q .url)"
}
EOF
            exit 2
        else
            echo "✅ GitHub Actions passed successfully" >&2
        fi
    else
        echo "⚠️  No GitHub Actions run found. Continuing..." >&2
    fi
fi

exit 0
```

### Pattern 4: TDD Enforcement (UserPromptSubmit)

**Problem:** Claude might write implementation before tests.

**Solution:** Inject TDD reminder into context when implementation is requested.

```bash
#!/bin/bash
# scripts/hooks/user_prompt_submit.sh

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt')

# Check if user is asking to implement something
if echo "$PROMPT" | grep -qiE "implement|add feature|create function|write.*code"; then
    # Check if tests exist for this feature
    # (This is simplified - real implementation would be more sophisticated)

    cat <<EOF
{
  "additionalContext": "REMINDER: Follow TDD process:\n1. Write failing test first\n2. Run test to confirm failure\n3. Implement minimal code to pass\n4. Run test to confirm pass\n5. Refactor if needed\n\nSee .claude/CLAUDE.md for complete TDD requirements."
}
EOF
fi

exit 0
```

### Pattern 5: Complexity Check (PostToolUse on Write/Edit)

**Problem:** Claude writes overly complex code.

**Solution:** Check cyclomatic complexity after file writes.

```bash
#!/bin/bash
# scripts/hooks/post_write.sh

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only check Python files after Write or Edit
if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
    if [[ "$FILE_PATH" =~ \.py$ ]]; then
        # Run complexity check on the file
        RESULT=$(radon cc "$FILE_PATH" -a -nb)

        # Check if average complexity is too high
        AVG_COMPLEXITY=$(echo "$RESULT" | grep "Average complexity" | awk '{print $NF}' | sed 's/[()]//g')

        if [ -n "$AVG_COMPLEXITY" ]; then
            # Convert to number and compare (bash doesn't do floating point)
            AVG_INT=$(echo "$AVG_COMPLEXITY" | awk '{print int($1)}')

            if [ "$AVG_INT" -gt 10 ]; then
                cat >&2 <<EOF
{
  "decision": "block",
  "reason": "Code complexity too high (CC=$AVG_COMPLEXITY). Please refactor to reduce complexity below 10.",
  "additionalContext": "Run './scripts/check_complexity.sh' for details. See docs/reference/CODE_QUALITY.md for guidelines."
}
EOF
                exit 2
            fi
        fi
    fi
fi

exit 0
```

### Pattern 6: Documentation Update Reminder (PostToolUse on Edit)

**Problem:** Claude modifies API but forgets to update documentation.

**Solution:** Remind Claude to update docs when API changes.

```bash
#!/bin/bash
# scripts/hooks/post_edit.sh

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Check if editing main API file
if [[ "$FILE_PATH" =~ src/omnifocus_mcp/client\.py ]]; then
    # Check if function signatures changed
    OLD_STRING=$(echo "$INPUT" | jq -r '.tool_input.old_string // empty')
    NEW_STRING=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')

    if echo "$OLD_STRING" | grep -q "^def " || echo "$NEW_STRING" | grep -q "^def "; then
        cat <<EOF
{
  "systemMessage": "⚠️  API function modified. Remember to update:\n- docs/API_REFERENCE.md\n- Docstrings\n- CHANGELOG.md (if breaking change)\n- Tests (unit, integration, e2e)"
}
EOF
    fi
fi

exit 0
```

---

## Session Context Loading (SessionStart)

**Use case:** Load project-specific context at the start of each session to inform Claude's decisions.

```bash
#!/bin/bash
# scripts/hooks/session_start.sh

echo "Loading OmniFocus MCP project context..." >&2

# Prepare context to inject into session
CONTEXT="# Current Project State\n\n"

# Add git status
CONTEXT+="## Git Status\n\`\`\`\n$(git status --short)\n\`\`\`\n\n"

# Add current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
CONTEXT+="**Current branch:** $BRANCH\n\n"

# Warn if on main
if [ "$BRANCH" = "main" ]; then
    CONTEXT+="⚠️  **WARNING:** You are on the main branch. Create a feature branch before making changes.\n\n"
fi

# Add open issues count
OPEN_ISSUES=$(gh issue list --state open --json number -q 'length')
CONTEXT+="**Open issues:** $OPEN_ISSUES\n\n"

# Add recent commits
CONTEXT+="## Recent Commits\n\`\`\`\n$(git log --oneline -5)\n\`\`\`\n\n"

# Return context as JSON
cat <<EOF
{
  "additionalContext": "$(echo -e "$CONTEXT" | jq -Rs .)"
}
EOF

exit 0
```

**Special feature:** Use `CLAUDE_ENV_FILE` to persist environment variables:

```bash
#!/bin/bash
# scripts/hooks/session_start.sh

# Set environment variables for subsequent Bash tool calls
if [ -n "$CLAUDE_ENV_FILE" ]; then
    echo 'export OMNIFOCUS_TEST_MODE=true' >> "$CLAUDE_ENV_FILE"
    echo 'export PYTHONPATH="$CLAUDE_PROJECT_DIR/src:$PYTHONPATH"' >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

---

## Transcript Preservation (PreCompact)

**Use case:** Back up conversation history before context compaction.

```bash
#!/bin/bash
# scripts/hooks/pre_compact.sh

INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')

# Create backup directory
BACKUP_DIR=".claude/transcript_backups"
mkdir -p "$BACKUP_DIR"

# Copy transcript with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp "$TRANSCRIPT_PATH" "$BACKUP_DIR/transcript_${SESSION_ID}_${TIMESTAMP}.json"

echo "Transcript backed up to $BACKUP_DIR/transcript_${SESSION_ID}_${TIMESTAMP}.json" >&2

exit 0
```

---

## Best Practices

### 1. Start Simple, Add Strictness Gradually

**Phase 1:** Informational hooks (systemMessage, warnings)
- Hook reports issues but doesn't block
- Claude learns what's expected
- You observe false positives

**Phase 2:** Blocking hooks (exit 2, decision: "block")
- After validating hook logic, make it blocking
- Claude cannot continue until issue is resolved
- System ratchets toward better behavior

### 2. Provide Clear Error Messages

```bash
# ❌ Bad: Cryptic error
echo "Error: condition failed" >&2
exit 2

# ✅ Good: Actionable error with context
cat >&2 <<EOF
{
  "decision": "block",
  "reason": "Tests must pass before committing (3 failures detected)",
  "additionalContext": "Run 'make test' to see failures. Fix all errors before committing."
}
EOF
exit 2
```

### 3. Use Timeouts Appropriately

```json
{
  "type": "command",
  "command": "./scripts/hooks/monitor_ci.sh",
  "timeout": 300  // 5 minutes for CI monitoring
}
```

**Guidelines:**
- Quick validation checks: 5-10 seconds
- Git operations: 30 seconds
- CI monitoring: 300 seconds (5 minutes)
- Complex analysis: 60 seconds

### 4. Handle Missing Dependencies Gracefully

```bash
#!/bin/bash

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "⚠️  gh CLI not found. Skipping GitHub Actions check." >&2
    echo "Install: brew install gh" >&2
    exit 0  # Don't block, just warn
fi

# Proceed with gh commands...
```

### 5. Log Hook Execution for Debugging

```bash
#!/bin/bash

LOG_FILE=".claude/hook_logs/$(date +%Y%m%d).log"
mkdir -p "$(dirname "$LOG_FILE")"

{
    echo "=== $(date) ==="
    echo "Hook: pre_bash.sh"
    echo "Input: $INPUT"
    echo "---"
} >> "$LOG_FILE"

# Hook logic...
```

### 6. Version Control Hook Scripts

- ✅ **Check in:** `.claude/settings.json` and `scripts/hooks/` directory
- ✅ **Document:** Each hook in `docs/reference/CLAUDE_CODE_HOOKS.md`
- ❌ **Don't check in:** `.claude/settings.local.json` (personal overrides)

### 7. Test Hooks Manually Before Enabling

```bash
# Simulate hook input
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}' | \
  ./scripts/hooks/pre_bash.sh

# Check exit code
echo $?

# Verify JSON output format
echo '{"tool_name":"Bash","tool_input":{"command":"git push"}}' | \
  ./scripts/hooks/post_bash.sh | jq .
```

---

## Hook Execution Flow

### PreToolUse Flow

```
User prompt → Claude plans tool use → PreToolUse hook fires
                                              ↓
                                    Hook returns JSON/exit code
                                              ↓
                              ┌───────────────┴───────────────┐
                              ↓                               ↓
                        exit 0 / allow                  exit 2 / deny
                              ↓                               ↓
                      Tool executes                   Tool blocked
                              ↓                               ↓
                      PostToolUse hook            Error shown to Claude
```

### PostToolUse Flow

```
Tool completes → PostToolUse hook fires → Validates results
                                                  ↓
                                    ┌─────────────┴─────────────┐
                                    ↓                           ↓
                              exit 0 / pass                exit 2 / fail
                                    ↓                           ↓
                            Claude continues        Error fed to Claude
                                                            ↓
                                                Claude must address error
```

### Stop Flow

```
Claude finishes response → Stop hook fires → Validates completion
                                                    ↓
                                      ┌─────────────┴─────────────┐
                                      ↓                           ↓
                                exit 0 / pass                exit 2 / block
                                      ↓                           ↓
                          Session can end          Claude forced to continue
                                                            ↓
                                                  Must complete checklist
```

---

## Integration with Issue Tracking

### Closed Loop: Issue → Prevention → Hook → Detection

1. **Issue filed** (e.g., #37: "Worked directly on main branch")
2. **Prevention designed** (documented in issue body)
3. **Hook implemented** (e.g., `pre_bash.sh` checks branch)
4. **Recurrence detection** (CI runs prevention script from issue body)
5. **Enforcement** (hook blocks Claude if violation attempted)

**Example workflow:**

```
Issue #37: Worked on main branch
    ↓
Prevention measure documented:
  "Block commits to main unless hotfix"
    ↓
Hook implemented:
  scripts/hooks/pre_bash.sh checks branch
    ↓
Hook enabled in .claude/settings.json
    ↓
CI checks prevention (./scripts/check_recurrence.sh)
    ↓
If Claude attempts commit on main:
  Hook blocks with error message
    ↓
CI passes (prevention working)
```

### Prevention Script Format in Issues

When filing AI process issues, include executable prevention script:

```markdown
## Prevention Script

```bash
# Check if hook exists and is enabled
if [ -f "scripts/hooks/pre_bash.sh" ] && \
   grep -q "pre_bash.sh" .claude/settings.json; then
    exit 0  # Prevention in place
else
    exit 1  # Prevention missing
fi
```
```

**CI will:**
1. Fetch open `ai-process` issues
2. Extract prevention script from issue body
3. Execute script
4. Report if prevention is not working (exit code != 0)

---

## Recommended Hooks for OmniFocus MCP

Based on issues #37 and #39, here's a suggested hook configuration:

| Hook | Event | Purpose | Strictness |
|------|-------|---------|------------|
| `pre_bash.sh` | PreToolUse(Bash) | Block commits to main, validate destructive commands | Blocking (exit 2) |
| `post_bash.sh` | PostToolUse(Bash) | Monitor CI after git push | Blocking (exit 2) if CI fails |
| `pre_stop.sh` | Stop | Verify tests pass before completion | Blocking (exit 2) if tests failing |
| `post_write.sh` | PostToolUse(Write) | Check code complexity | Warning initially, blocking at CC > 20 |
| `post_edit.sh` | PostToolUse(Edit) | Remind to update docs when API changes | Warning only |
| `session_start.sh` | SessionStart | Load project context, warn if on main | Context injection |
| `pre_compact.sh` | PreCompact | Backup transcript before memory loss | Non-blocking (exit 0) |

**Implementation priority:**
1. ✅ **High:** `pre_bash.sh` (addresses #37), `post_bash.sh` (addresses #39)
2. ⚠️ **Medium:** `pre_stop.sh` (TDD enforcement)
3. 📋 **Low:** Other hooks (nice-to-have)

---

## Limitations and Considerations

### What Hooks Cannot Do

- **Cannot prevent User from interrupting** - Users can always Ctrl-C
- **Cannot modify tool parameters** - Can only allow/deny in PreToolUse
- **Cannot access external APIs** (unless via curl/gh in hook script)
- **Cannot persist state** between hook invocations (use files or transcript)
- **Cannot block SessionEnd** - Only cleanup actions possible

### Performance Considerations

- **Hooks run synchronously** - Slow hooks block Claude
- **Parallel execution** - Multiple matching hooks run concurrently
- **Timeout is enforced** - Hook killed after timeout, treated as failure
- **Transcript access** - Reading large transcripts can be slow

### Security Considerations

- **Hooks run arbitrary shell commands** - Malicious hooks can compromise system
- **Configuration snapshot at startup** - Mid-session config changes ignored (security feature)
- **Path traversal risks** - Validate file paths in hooks
- **Sensitive data** - Don't log passwords, API keys, etc. in hook output

---

## Testing Hooks

### Manual Testing

```bash
# Test PreToolUse hook
echo '{
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {"command": "git commit -m \"test\""},
  "cwd": "'$(pwd)'"
}' | ./scripts/hooks/pre_bash.sh

# Test PostToolUse hook
echo '{
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": {"command": "git push"},
  "tool_response": {"exit_code": 0},
  "cwd": "'$(pwd)'"
}' | ./scripts/hooks/post_bash.sh

# Test Stop hook
echo '{
  "hook_event_name": "Stop",
  "stop_hook_active": true,
  "transcript_path": "'$(mktemp)'",
  "cwd": "'$(pwd)'"
}' | ./scripts/hooks/pre_stop.sh
```

### Automated Testing

Create test suite for hooks:

```bash
#!/bin/bash
# tests/test_hooks.sh

set -e

echo "Testing hooks..."

# Test 1: pre_bash.sh blocks commits to main
echo "Test: Block commit on main branch"
git checkout main
RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}' | \
  ./scripts/hooks/pre_bash.sh 2>&1)
if [ $? -eq 2 ]; then
    echo "✅ PASS: Commit blocked on main branch"
else
    echo "❌ FAIL: Commit should be blocked on main branch"
    exit 1
fi

# Test 2: pre_bash.sh allows commits on feature branch
echo "Test: Allow commit on feature branch"
git checkout -b test-branch
RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}' | \
  ./scripts/hooks/pre_bash.sh 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ PASS: Commit allowed on feature branch"
else
    echo "❌ FAIL: Commit should be allowed on feature branch"
    exit 1
fi

git checkout main
git branch -D test-branch

echo "All tests passed!"
```

---

## Migration Path

### Phase 1: Observation (Week 1)

1. Implement hooks with **informational mode** only (exit 0, systemMessage)
2. Monitor Claude's behavior and hook output
3. Identify false positives and edge cases
4. Refine hook logic

### Phase 2: Enforcement (Week 2)

1. Switch to **blocking mode** (exit 2, decision: "block")
2. Document any issues Claude encounters
3. Adjust error messages for clarity
4. Verify CI detects missing hooks

### Phase 3: Optimization (Week 3+)

1. Add more sophisticated hooks based on new issues
2. Tune timeouts and performance
3. Create hook test suite
4. Document lessons learned

---

## Resources

- **Official docs:** https://docs.claude.com/en/docs/claude-code/hooks
- **Example repo:** https://github.com/disler/claude-code-hooks-mastery
- **This project's hooks:** `scripts/hooks/` directory
- **Issue tracking:** GitHub Issues with `ai-process` label
- **CI validation:** `.github/workflows/mistake-tracking.yml`

---

## Next Steps

1. **Review this document** - Ensure understanding of hook capabilities
2. **Design hooks for #37 and #39** - Start with these two issues
3. **Implement in phases** - Informational → Blocking → Optimized
4. **Update prevention scripts** - Issues should reference hook files
5. **Test thoroughly** - Manual and automated testing before enabling
6. **Monitor and iterate** - Adjust based on real-world usage

**See:** Issue #40 (proposed) - "Implement Claude Code hooks for issues #37 and #39"
