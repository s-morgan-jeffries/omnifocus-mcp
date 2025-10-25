# Hook Systems Documentation - Navigation Guide

This project uses **two hook systems** for workflow enforcement: **Git hooks** and **Claude Code hooks**.

This guide helps you find the right documentation for your needs.

## Quick Reference

| Your Question | Document |
|---------------|----------|
| "What are hooks and why do we use them?" | [HOOKS_COMPARISON.md](#hooks-comparison) - Start here |
| "How do I write a Claude Code hook?" | [CLAUDE_CODE_HOOKS.md](#claude-code-hooks) - Implementation guide |
| "Which hook solves issue #X?" | [HOOK_SOLUTIONS_FOR_ALL_ISSUES.md](#hook-solutions) - Issue mapping |
| "What hooks are currently active?" | [CLAUDE_CODE_HOOKS.md](CLAUDE_CODE_HOOKS.md#active-hooks) |
| "How do I install git hooks?" | Run `./scripts/install-git-hooks.sh` |
| "How do I test hooks?" | See [tests/test_claude_code_hooks.py](../../tests/test_claude_code_hooks.py) |

## Documentation Files

### HOOKS_COMPARISON.md
**Purpose:** Strategic comparison of hook systems

**Read this first if:**
- You're new to the project
- You want to understand why we have two hook systems
- You're deciding which hook type to use for a new check

**Contents:**
- Git Hooks vs GitHub Actions vs Claude Code hooks vs pre-commit framework
- When to use each system
- Tradeoffs and limitations
- Our hybrid approach (git hooks + Claude Code hooks)

**Length:** ~400 lines | **Audience:** All contributors

---

### CLAUDE_CODE_HOOKS.md
**Purpose:** Complete implementation guide for Claude Code hooks

**Read this if:**
- You're implementing a new Claude Code hook
- You want to understand how hooks work technically
- You need to modify existing hook behavior

**Contents:**
- How Claude Code hooks work (PreToolUse, PostToolUse, SessionStart, etc.)
- Hook configuration in `.claude/settings.json`
- Script structure and modular design
- Examples for all hook types
- Testing and debugging
- Best practices

**Length:** ~880 lines | **Audience:** Hook developers

---

### HOOK_SOLUTIONS_FOR_ALL_ISSUES.md
**Purpose:** Map project issues to hook-based solutions

**Read this if:**
- You're working on an `ai-process` issue
- You want to prevent a specific type of mistake
- You're evaluating whether hooks can solve your problem

**Contents:**
- Analysis of all 13 `ai-process` issues
- Hook-based prevention strategies for each
- Which hook types solve which problems
- Implementation examples

**Length:** ~730 lines | **Audience:** Issue fixers, workflow designers

---

## Active Hook Systems

### Git Hooks (Secondary)

**Location:** `scripts/git-hooks/`
**Installation:** `./scripts/install-git-hooks.sh`

**Active hooks:**
- `pre-commit` - Validates commits (tests exist, issue references, etc.)
- `commit-msg` - Formats commit messages
- `pre-tag` - Enforces release hygiene for RC/final tags

**Use case:** Backup enforcement when not using Claude Code

### Claude Code Hooks (Primary)

**Location:** `scripts/hooks/`
**Configuration:** `.claude/settings.json`

**Active hooks:**
- `PreToolUse(Bash)` - Blocks commits to main, prevents RC tagging through Claude
- `PostToolUse(Bash)` - Monitors GitHub Actions after git push
- `SessionStart` - Loads project context (branch, issues, milestone)

**Use case:** Primary enforcement during AI coding sessions

## Common Tasks

### Adding a New Check to Pre-Commit Hook

1. Edit `scripts/git-hooks/pre-commit`
2. Add new `check_*` function (see existing examples)
3. Add function name to `CHECKS` array
4. Test: `./scripts/git-hooks/pre-commit` (will run on current repo state)
5. Reinstall: `./scripts/install-git-hooks.sh`

### Adding a New Check to Claude Code Hook

1. Edit `scripts/hooks/pre_bash.sh` (or `post_bash.sh`, `session_start.sh`)
2. Add new `check_*` function following modular pattern
3. Add function name to `CHECKS` array
4. Test: `echo '{"tool_name":"Bash",...}' | ./scripts/hooks/pre_bash.sh`
5. Restart Claude Code session to pick up changes

### Testing Hooks

**Git hooks:**
```bash
# Test specific hook manually
./scripts/git-hooks/pre-commit
./scripts/git-hooks/pre-tag v0.6.4-rc1

# Unit tests
pytest tests/test_claude_code_hooks.py
```

**Claude Code hooks:**
```bash
# Test specific hook manually (JSON on stdin)
echo '{"tool_name":"Bash","parameters":{"command":"git commit -m test"}}' | ./scripts/hooks/pre_bash.sh

# Unit tests
pytest tests/test_claude_code_hooks.py -k claude_code
```

## Design Philosophy

**Why two systems?**

1. **Claude Code hooks** are primary - they catch issues during AI coding sessions (the main workflow)
2. **Git hooks** are backup - they catch issues during manual git operations

Both systems coexist and complement each other. See [HOOKS_COMPARISON.md](HOOKS_COMPARISON.md) for full rationale.

## Related Documentation

- **Active hooks explained:** [../../.claude/CLAUDE.md](../../.claude/CLAUDE.md#claude-code-hooks-automated-enforcement)
- **Git vs Claude Code hooks:** [HOOKS_COMPARISON.md](HOOKS_COMPARISON.md)
- **Implementation guide:** [CLAUDE_CODE_HOOKS.md](CLAUDE_CODE_HOOKS.md)
- **Issue solutions:** [HOOK_SOLUTIONS_FOR_ALL_ISSUES.md](HOOK_SOLUTIONS_FOR_ALL_ISSUES.md)
- **Test suite:** [../../tests/test_claude_code_hooks.py](../../tests/test_claude_code_hooks.py)
