# Hooks Comparison: Git, GitHub Actions, and Claude Code

**Purpose:** Quick reference comparing different hook systems and when to use each.

**Last Updated:** 2025-10-25

---

## Hook Systems Overview

| System | Runs Where | Triggered By | Affects Who | Best For |
|--------|------------|--------------|-------------|----------|
| **Git Hooks** | Local repository | Git commands (commit, push, etc.) | Everyone with repo clone | Local validation before commits/pushes |
| **GitHub Actions** | GitHub servers | Push, PR, schedule, manual | Everyone (CI/CD for all contributors) | Automated testing, deployment, public validation |
| **Claude Code Hooks** | During Claude session | Claude tool use, session events | Only Claude Code sessions | AI behavior enforcement, process compliance |
| **Pre-commit Framework** | Local repository | Git commit | Developers who install it | Code formatting, linting, local checks |

---

## Hook System Details

### Git Hooks

**Location:** `.git/hooks/` (not version controlled by default)

**Available hooks:**
- `pre-commit` - Before commit is created
- `prepare-commit-msg` - Before commit message editor opens
- `commit-msg` - After commit message is written
- `post-commit` - After commit is created
- `pre-push` - Before push to remote
- `post-checkout` - After checking out branch
- `post-merge` - After merge completes

**Pros:**
- ✅ Fast (runs locally)
- ✅ Prevents bad commits from being created
- ✅ Can modify commits before they're finalized
- ✅ Works with all Git tools

**Cons:**
- ❌ Not version controlled (requires setup scripts)
- ❌ Can be bypassed with `--no-verify`
- ❌ Affects all developers (may slow down workflow)
- ❌ Requires manual installation

**Use for:**
- Running tests before commits
- Validating commit message format
- Running linters/formatters
- Preventing commits to protected branches locally

**When to use in OmniFocus MCP:**
- ✅ Running integration/e2e tests locally (not in GitHub Actions)
- ✅ Commit message validation
- ⚠️ Pre-commit test running (can slow down commits)

---

### GitHub Actions (CI/CD)

**Location:** `.github/workflows/` (version controlled)

**Triggered by:**
- Push to branches
- Pull requests
- Schedules (cron)
- Manual dispatch
- Issue events
- Release events

**Pros:**
- ✅ Version controlled
- ✅ Cannot be bypassed
- ✅ Runs on clean environment
- ✅ Visible to all team members
- ✅ Required status checks block merges

**Cons:**
- ❌ Slower than local hooks (queue time, cold starts)
- ❌ Costs money (minutes/storage for private repos)
- ❌ Feedback loop longer than local validation
- ❌ Can't run integration tests requiring local OmniFocus

**Use for:**
- Unit tests (mocked)
- Code coverage reporting
- Linting and formatting checks
- Building and deploying
- Recurrence detection (checking prevention scripts)

**Currently used in OmniFocus MCP:**
- ✅ Unit tests (`make test`)
- ✅ Recurrence checking (`scripts/check_recurrence.sh`)
- ❌ Integration tests (require local OmniFocus, can't run in CI)

---

### Claude Code Hooks

**Location:** `.claude/settings.json` (version controlled) or `~/.claude/settings.json` (global)

**Available events:**
- `PreToolUse` - Before tool execution (can block)
- `PostToolUse` - After tool execution (can inform Claude)
- `UserPromptSubmit` - Before processing prompt (can add context)
- `Stop` - Before Claude finishes (can force continuation)
- `SubagentStop` - When subagent completes (can reject result)
- `SessionStart` - Session begins (can inject context)
- `SessionEnd` - Session terminates (cleanup only)
- `PreCompact` - Before context compaction (can backup)
- `Notification` - Permission requests (informational)

**Pros:**
- ✅ AI-specific enforcement (doesn't affect humans)
- ✅ Version controlled (when in project `.claude/settings.json`)
- ✅ Can block Claude from continuing
- ✅ Can inject context into sessions
- ✅ Fast (runs locally during session)

**Cons:**
- ❌ Only affects Claude Code sessions
- ❌ Requires shell scripting knowledge
- ❌ Timeout limits (60s default)
- ❌ Cannot block user interruptions
- ❌ Relatively new feature (less documentation)

**Use for:**
- Enforcing TDD workflow (block if no tests)
- Branch validation (prevent commits to main)
- Monitoring CI after push
- Loading project context at session start
- Checking code complexity after writes
- Reminding about documentation updates

**Proposed for OmniFocus MCP:**
- 🔄 Branch validation (issue #37)
- 🔄 CI monitoring (issue #39)
- 📋 TDD enforcement (future)
- 📋 Complexity checks (future)

---

### Pre-commit Framework

**Location:** `.pre-commit-config.yaml` (version controlled)

**Language:** Python-based framework with plugins for many languages

**Available hooks:** Hundreds via plugins:
- `black` - Python formatter
- `flake8` - Python linter
- `mypy` - Python type checker
- `prettier` - JavaScript/TypeScript formatter
- `eslint` - JavaScript linter
- Many more...

**Pros:**
- ✅ Easy to configure (YAML)
- ✅ Large ecosystem of plugins
- ✅ Manages hook installation automatically
- ✅ Version controlled
- ✅ Fast (cached results)

**Cons:**
- ❌ Requires installation (`pip install pre-commit`)
- ❌ Adds dependency to project
- ❌ Can slow down commits (if hooks are slow)
- ❌ Can be bypassed with `--no-verify`

**Use for:**
- Code formatting (automatic fixes)
- Linting (catch errors before commit)
- Type checking
- Security scanning
- Testing (if tests are fast)

**When to use in OmniFocus MCP:**
- 📋 Future consideration when team grows
- 📋 Useful for enforcing Python formatting (black, isort)
- 📋 Type checking with mypy
- ⚠️ May be overkill for solo development

---

## Comparison Table: What Problems Each System Catches

| Problem | Git Hook | GitHub Actions | Claude Code Hook | Pre-commit |
|---------|----------|----------------|------------------|------------|
| **Syntax errors** | ✅ pre-commit | ✅ CI tests | ❌ No | ✅ lint hook |
| **Test failures** | ✅ pre-commit/pre-push | ✅ CI tests | ✅ Stop hook | ✅ test hook |
| **Forgot to run tests** | ✅ pre-commit runs them | ✅ CI runs them | ✅ Stop hook checks | ✅ test hook |
| **AI didn't monitor CI** | ❌ Not AI-aware | ❌ Runs after push | ✅ PostToolUse hook | ❌ Not AI-aware |
| **AI violated TDD** | ❌ Not AI-aware | ❌ Hard to detect | ✅ PreToolUse/Stop hook | ❌ Not AI-aware |
| **Wrong branch** | ✅ pre-commit checks | ⚠️ Can detect but too late | ✅ PreToolUse hook | ✅ check hook |
| **Code complexity** | ✅ pre-commit checks | ✅ CI checks | ✅ PostToolUse hook | ✅ radon hook |
| **Type errors** | ✅ pre-commit mypy | ✅ CI mypy | ⚠️ Could via PostToolUse | ✅ mypy hook |
| **Formatting issues** | ✅ pre-commit formats | ✅ CI checks | ❌ No | ✅ black/prettier |
| **Security issues** | ✅ pre-commit scan | ✅ CI scan | ⚠️ Could block dangerous commands | ✅ bandit hook |
| **Missing docs** | ⚠️ Hard to detect | ⚠️ Hard to detect | ✅ PostToolUse reminder | ❌ No |
| **Incomplete checklist** | ❌ No | ❌ No | ✅ Stop hook | ❌ No |

**Legend:**
- ✅ Well-suited for this problem
- ⚠️ Possible but not ideal
- ❌ Not designed for this
- 🔄 Proposed/in progress
- 📋 Future consideration

---

## Recommended Strategy for OmniFocus MCP

### Current Setup (What You Have)

| System | Status | Purpose |
|--------|--------|---------|
| **GitHub Actions** | ✅ Active | Unit tests, recurrence detection |
| **Git Hooks** | ❌ None | Not currently used |
| **Claude Code Hooks** | ❌ None | Proposed in issues #37, #39 |
| **Pre-commit** | ❌ None | Not currently used |

### Recommended Implementation (Prioritized)

#### Phase 1: Claude Code Hooks (High Priority)

**Why first:** Addresses immediate AI process failures (issues #37, #39) without affecting your manual workflow.

| Hook | Event | Purpose | Priority |
|------|-------|---------|----------|
| `pre_bash.sh` | PreToolUse(Bash) | Block commits to main branch | 🔴 High |
| `post_bash.sh` | PostToolUse(Bash) | Monitor CI after git push | 🔴 High |
| `pre_stop.sh` | Stop | Verify tests pass before completion | 🟡 Medium |
| `session_start.sh` | SessionStart | Load project context, warn if on main | 🟡 Medium |
| `post_write.sh` | PostToolUse(Write) | Check code complexity after writes | 🟢 Low |
| `post_edit.sh` | PostToolUse(Edit) | Remind to update docs on API changes | 🟢 Low |

**Implementation order:**
1. Start with **informational mode** (warnings only)
2. Monitor for false positives
3. Switch to **blocking mode** after validation
4. Update issue prevention scripts to check for hooks

#### Phase 2: Git Hooks (Medium Priority)

**Why second:** Useful for running integration/e2e tests locally (can't run in GitHub Actions).

| Hook | Purpose | Priority |
|------|---------|----------|
| `pre-push` | Run integration/e2e tests before push | 🟡 Medium |
| `commit-msg` | Validate commit message format | 🟢 Low |

**Trade-offs:**
- ✅ Catches issues before they reach remote
- ✅ Can run integration tests requiring local OmniFocus
- ❌ Slows down your workflow (tests take time)
- ❌ Affects you even when not using Claude Code

**Recommendation:** Implement `pre-push` for integration tests, make it skippable with `--no-verify` for quick pushes.

#### Phase 3: Pre-commit Framework (Low Priority)

**Why last:** Most useful when team grows; overkill for solo development.

**Consider when:**
- Multiple contributors join project
- You want automatic formatting (black, isort)
- You want type checking before every commit (mypy)

**For now:** Stick with GitHub Actions for linting/formatting checks.

---

## Decision Matrix: Which Hook System to Use

| Goal | Recommended System | Why |
|------|-------------------|-----|
| **Prevent AI from working on main** | Claude Code Hook (PreToolUse) | AI-specific, doesn't affect you |
| **Make AI monitor CI after push** | Claude Code Hook (PostToolUse) | AI-specific, automated monitoring |
| **Enforce TDD for AI** | Claude Code Hook (Stop) | AI-specific, blocks completion |
| **Run integration tests locally** | Git Hook (pre-push) | Can't run in GitHub Actions |
| **Run unit tests for everyone** | GitHub Actions (CI) | Public validation, can't bypass |
| **Format code automatically** | Pre-commit Framework | Easy setup, large ecosystem |
| **Check code complexity** | GitHub Actions + Claude Code Hook | CI for everyone, hook blocks AI |
| **Validate commit messages** | Git Hook (commit-msg) | Local, fast feedback |
| **Security scanning** | GitHub Actions (CI) | Permanent record, can't bypass |
| **Load project context for AI** | Claude Code Hook (SessionStart) | AI-specific, injected automatically |

---

## Hook Strictness Comparison

| System | Can Block? | Can Be Bypassed? | Affects Who? |
|--------|------------|------------------|--------------|
| **Git Hook (pre-commit)** | ✅ Yes (prevents commit) | ✅ Yes (`--no-verify`) | All developers |
| **Git Hook (pre-push)** | ✅ Yes (prevents push) | ✅ Yes (`--no-verify`) | All developers |
| **GitHub Actions** | ✅ Yes (blocks PR merge) | ❌ No (if required status check) | All contributors |
| **Claude Code Hook (PreToolUse)** | ✅ Yes (blocks tool) | ❌ No (Claude must comply) | Only Claude |
| **Claude Code Hook (Stop)** | ✅ Yes (forces continuation) | ⚠️ User can interrupt | Only Claude |
| **Pre-commit Framework** | ✅ Yes (prevents commit) | ✅ Yes (`--no-verify`) | All developers |

**Key insight:** GitHub Actions (with required status checks) and Claude Code Hooks are the **only systems that cannot be easily bypassed**.

---

## Behavioral Enforcement Matrix

| Behavior to Enforce | Git Hook | GitHub Actions | Claude Code Hook | Pre-commit |
|---------------------|----------|----------------|------------------|------------|
| **Tests pass before commit** | ✅ pre-commit | ✅ CI (but too late) | ✅ Stop hook | ✅ test hook |
| **Code formatted correctly** | ✅ pre-commit | ✅ CI checks | ❌ No | ✅ format hook |
| **No commits to main** | ✅ pre-commit | ⚠️ Branch protection | ✅ PreToolUse | ✅ branch check |
| **Monitor CI after push** | ❌ No | ❌ No | ✅ PostToolUse | ❌ No |
| **Update docs when API changes** | ❌ No | ⚠️ Can check | ✅ PostToolUse | ❌ No |
| **Follow TDD process** | ❌ Hard to enforce | ❌ Hard to enforce | ✅ PreToolUse/Stop | ❌ No |
| **Load project context** | ❌ No | ❌ No | ✅ SessionStart | ❌ No |
| **Check code complexity** | ✅ pre-commit | ✅ CI | ✅ PostToolUse | ✅ radon hook |

---

## Implementation Phases

### Phase 1: Foundation (Week 1) - Claude Code Hooks

**Goal:** Prevent recurrence of issues #37 and #39

**Actions:**
1. Create `scripts/hooks/` directory
2. Implement `pre_bash.sh` (branch validation)
3. Implement `post_bash.sh` (CI monitoring)
4. Configure `.claude/settings.json`
5. Test in informational mode
6. Switch to blocking mode after validation
7. Update issue prevention scripts

**Success criteria:**
- ✅ Claude blocked from committing to main
- ✅ Claude monitors CI after every push
- ✅ CI detects if hooks are missing

### Phase 2: Expansion (Week 2-3) - More Claude Hooks

**Goal:** Enforce TDD and code quality

**Actions:**
1. Implement `pre_stop.sh` (test validation)
2. Implement `session_start.sh` (context loading)
3. Implement `post_write.sh` (complexity checks)
4. Implement `post_edit.sh` (doc reminders)
5. Create hook test suite

**Success criteria:**
- ✅ Claude runs tests before completing
- ✅ Claude reminded of TDD process
- ✅ Claude warned about complex code
- ✅ All hooks tested automatically

### Phase 3: Local Validation (Week 4+) - Git Hooks

**Goal:** Run integration tests locally

**Actions:**
1. Create `scripts/git_hooks/pre-push`
2. Install script: `ln -s ../../scripts/git_hooks/pre-push .git/hooks/`
3. Run integration/e2e tests before push
4. Document skipping with `--no-verify` for quick pushes

**Success criteria:**
- ✅ Integration tests run before push
- ✅ Can skip for quick iterations
- ✅ Catches OmniFocus-specific issues locally

### Phase 4: Team Scale (Future) - Pre-commit Framework

**Goal:** Ready for team contributions

**Actions:**
1. Add `.pre-commit-config.yaml`
2. Configure black, isort, mypy, radon
3. Document installation in CONTRIBUTING.md
4. Add CI check that pre-commit hooks pass

**Success criteria:**
- ✅ Consistent formatting across contributors
- ✅ Type errors caught before commit
- ✅ Easy for new contributors to set up

---

## Cost-Benefit Analysis

| System | Setup Cost | Runtime Cost | Maintenance | Benefit |
|--------|------------|--------------|-------------|---------|
| **Git Hooks** | Medium (write scripts) | Low (local, fast) | Low | High (fast feedback) |
| **GitHub Actions** | Low (YAML config) | Free (public repos) | Low | Very High (permanent validation) |
| **Claude Code Hooks** | Medium (write scripts) | Low (local, fast) | Medium | Very High (AI behavior control) |
| **Pre-commit** | Low (YAML config) | Low (cached) | Low | High (auto-formatting) |

**For OmniFocus MCP:**
- **Highest ROI:** Claude Code Hooks (addresses AI-specific issues)
- **Already have:** GitHub Actions (free, permanent validation)
- **Nice to have:** Git Hooks (integration tests), Pre-commit (when team grows)

---

## Next Steps

1. **Read:** [docs/reference/CLAUDE_CODE_HOOKS.md](CLAUDE_CODE_HOOKS.md) for implementation details
2. **File issue:** Create issue for implementing hooks for #37 and #39
3. **Implement Phase 1:** Branch validation and CI monitoring hooks
4. **Test thoroughly:** Manual and automated testing before enabling blocking mode
5. **Monitor:** Watch for false positives and refine
6. **Expand:** Add more hooks as new issues are identified
7. **Document:** Update CLAUDE.md with hook expectations

**Key principle:** Start with AI-specific hooks (Claude Code), expand to universal hooks (Git/pre-commit) only when needed.
