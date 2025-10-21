---
name: AI Process Failure
about: Log an AI workflow or architectural mistake
title: '[AI-PROCESS] '
labels: ['ai-process']
assignees: []
---

## What Happened

[Clear description of what went wrong]

## Context

- **File(s):**
- **Function(s):**
- **Commit:**
- **Discovery Date:** YYYY-MM-DD

## Impact

[How this affected the project or user]

## Root Cause

[Why this happened - what process/check was missing?]

## Prevention Measures

### Immediate Fix
[What was done to resolve this specific instance]

- **Resolved in commit:** [hash]

### Long-term Prevention
[How to prevent this class of mistakes]

- [ ] Prevention measure 1
- [ ] Prevention measure 2

## Prevention Script

```bash
# Bash script to verify prevention is working
# This script should exit 0 if prevention is in place, exit 1 if not
# Example:
# if grep -q "checklist item" .claude/CLAUDE.md; then
#     exit 0
# else
#     exit 1
# fi
```

## Related Issues

[Links to related issues, if any - especially duplicates indicating recurrence]
