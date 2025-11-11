# Hygiene Check Pass/Fail Criteria

**Purpose:** Define clear, objective criteria for all automated hygiene checks.

**Last Updated:** 2025-11-11 (v0.7.0 - Hygiene Check Reordering)

---

## Overview

Hygiene checks are split into two categories:

1. **Automated Checks** - Run on every RC tag, clear pass/fail, block release if fail
2. **Interactive Checks** - Run on-demand via slash commands, generate qualitative reports

This document defines the **automated check criteria** only. Interactive checks are documented in their respective slash command files.

---

## Automated Checks (Critical - Must Pass)

**Execution Order (as of v0.7.0):**

The checks are run in order of execution speed, with fast checks (1-6) running first, followed by slower checks (7-8). This provides faster feedback if early checks fail, avoiding the 20-25 minute wait for tests when faster checks would have caught issues.

- **Fast checks (~1-2s each):** Version sync, complexity, parity, milestone, ROADMAP sync, docs
- **Slow checks:** Test coverage (~30s), All tests (~20-25 min)

---

### 1. Version Synchronization (~1s)

**Script:** `scripts/check_version_sync.sh`

**Pass Criteria:**
- ✅ `pyproject.toml` contains version `X.Y.Z`
- ✅ `.claude/CLAUDE.md` contains `**Current Version:** vX.Y.Z`
- ✅ `CHANGELOG.md` contains `## [X.Y.Z]` section
- ✅ `README.md` contains `(vX.Y.Z API)` reference

**Fail Criteria:**
- ❌ Any file missing version reference
- ❌ Version numbers don't match across files
- ❌ Version format incorrect (must be semver: X.Y.Z)

**Exit Codes:**
- `0` - All files synchronized
- `1` - One or more files out of sync

---

### 2. Code Complexity (~2s)

**Script:** `scripts/check_complexity.sh`

**Pass Criteria:**
- ✅ All functions have Cyclomatic Complexity (CC) ≤ 20 (A, B, or C rating)
- ✅ Maintainability Index (MI) ≥ 10 (A or B rating)
- ✅ No functions with D or F complexity rating (CC > 20)

**Allowed Exceptions (documented):**
- `get_tasks()` - CC 21-30 acceptable (21 parameters, complex filtering logic)
- `update_task()` - CC 21-30 acceptable (extensive property handling)

**Fail Criteria:**
- ❌ Any function has CC > 30 (F rating) without documentation
- ❌ Any NEW function has CC > 20 (must be documented if added)
- ❌ Maintainability Index < 10 (C rating) for any file

**Exit Codes:**
- `0` - All complexity within acceptable limits
- `1` - One or more functions exceed limits

**Current Status:** Script runs but doesn't enforce thresholds (always exits 0). **Needs implementation.**

---

### 3. Client-Server Parity (~1s)

**Script:** `scripts/check_client_server_parity.sh`

**Pass Criteria:**
- ✅ All public functions in `omnifocus_client.py` have corresponding MCP tools in `server_fastmcp.py`
- ✅ Function names match (allowing for case conversion)
- ✅ No orphaned tools (tools without client functions)

**Fail Criteria:**
- ❌ Client function exists without MCP tool
- ❌ MCP tool exists without client function
- ❌ Function signatures don't match (parameter mismatch)

**Exit Codes:**
- `0` - Perfect parity
- `1` - One or more mismatches

---

### 4. Milestone Status (~1s)

**Script:** Inline in git pre-tag hook and GitHub Actions workflow

**Pass Criteria:**
- ✅ Milestone `vX.Y.Z` exists in GitHub
- ✅ Milestone has **zero open issues**
- ✅ Next milestone `vX.Y.Z+1` exists (warning only, not critical)

**Fail Criteria:**
- ❌ Milestone doesn't exist
- ❌ Milestone has open issues
- ❌ Cannot connect to GitHub API

**Exit Codes:**
- `0` - Milestone exists and has no open issues
- `1` - Milestone missing or has open issues

---

### 5. ROADMAP.md Synchronization (~2s)

**Script:** `scripts/check_roadmap_sync.sh`

**Pass Criteria:**
- ✅ All closed issues in milestone removed from "Upcoming Work" section
- ✅ All closed issues in milestone removed from "Known Bugs" section
- ✅ Closed issues may appear in "Completed" or version-specific sections

**Fail Criteria:**
- ❌ Any closed issue still appears in "Upcoming Work"
- ❌ Any closed issue still appears in "Known Bugs"
- ❌ Cannot fetch milestone issues from GitHub

**Exit Codes:**
- `0` - ROADMAP.md is synchronized with closed issues
- `1` - One or more closed issues still in active sections

**Status:** ✅ Working

---

### 6. Documentation Completeness (~2s)

**Script:** `scripts/check_documentation.sh`

**Pass Criteria:**
- ✅ `CHANGELOG.md` contains `## [X.Y.Z]` entry for this version
- ✅ `.claude/CLAUDE.md` has "Current Version: vX.Y.Z" updated
- ✅ `README.md` references version (warning only)
- ✅ If CHANGELOG mentions "breaking", migration guide exists: `docs/migration/vX.Y.Z.md`
- ✅ All key documentation files exist:
  - `docs/guides/TESTING.md`
  - `docs/guides/CONTRIBUTING.md`
  - `docs/guides/INTEGRATION_TESTING.md`
  - `docs/reference/ARCHITECTURE.md`
  - `docs/reference/CODE_QUALITY.md`
  - `docs/reference/APPLESCRIPT_GOTCHAS.md`
  - `docs/project/ROADMAP.md`

**Fail Criteria:**
- ❌ CHANGELOG missing entry for this version
- ❌ CLAUDE.md version not updated
- ❌ Breaking changes in CHANGELOG but no migration guide
- ❌ Any key documentation file missing

**Exit Codes:**
- `0` - All documentation checks passed
- `1` - One or more checks failed

**Status:** ✅ Implemented (integrated in v0.6.7, issue #124).

**Why this matters:**
- Prevents shipping breaking changes without migration guides
- Ensures documentation stays synchronized with code
- Catches accidentally deleted key docs before release
- Maintains professional changelog discipline

---

### 7. Test Coverage (~30s)

**Script:** `scripts/check_test_coverage.sh`

**Pass Criteria:**
- ✅ Overall coverage ≥ 85% (measured via pytest-cov)
- ✅ All public functions have test coverage
- ✅ No TODO test markers in source code

**Fail Criteria:**
- ❌ Overall coverage < 85%
- ❌ Public functions without test coverage
- ❌ TODO test markers indicating planned tests

**Exit Codes:**
- `0` - Coverage ≥ 85% and all criteria met
- `1` - Coverage < 85% or other criteria failed

**Note:** This was changed from an interactive check to a critical check in v0.6.6 to enforce minimum coverage standards.

---

### 8. All Tests Pass (~20-25 min)

**Script:** `scripts/run_all_tests.sh` (called by pre-tag hook)

**Pass Criteria:**
- ✅ All unit tests pass (pytest exit code 0)
- ✅ All integration tests pass (pytest exit code 0)
- ✅ All E2E tests pass (pytest exit code 0)
- ✅ No test failures, no test errors
- ✅ Skipped tests are expected (integration tests when no test DB)

**Fail Criteria:**
- ❌ Any test fails
- ❌ Any test has errors
- ❌ Test collection fails
- ❌ Import errors

**Exit Codes:**
- `0` - All tests passed
- `1` - One or more tests failed

**Note:**
- GitHub Actions only runs unit tests (integration/E2E require local OmniFocus setup)
- **As of v0.7.0:** Moved to last position in execution order (#132) to provide faster feedback from earlier checks

---

### Test Count Synchronization (Not in pre-tag hook)

**Script:** `scripts/check_test_count_sync.sh`

**Pass Criteria:**
- ✅ Actual test count (from pytest) matches documented count in `docs/guides/TESTING.md`
- ✅ Count includes only unit tests (excludes integration tests marked with `@pytest.mark.integration`)

**Fail Criteria:**
- ❌ Test count mismatch between pytest and documentation
- ❌ Cannot determine test count (pytest failure)

**Exit Codes:**
- `0` - Counts match
- `1` - Counts don't match or cannot determine

**Status:** ✅ Implemented and working (caught mismatch in v0.6.5).

**Note:** This check is NOT run as part of the pre-tag hook. It's available for manual execution when needed.

---

## Interactive Checks (Non-Blocking)

These checks are available via manual script execution for code quality insights. They provide recommendations but don't block releases.

### Documentation Quality

**Slash Command:** `/doc-quality` (**To be created** - issue #86)

**Purpose:** Qualitative assessment of documentation completeness and clarity

**Checks:**
- README completeness and accuracy
- Foundation model interpretability
- Cross-reference integrity
- Technical accuracy of examples
- Migration guide relevance

**Output:** Report with severity levels (critical, recommended, suggestions)

**Status:** ⏳ Not yet implemented (part of v0.6.6, issue #86).

---

### Code Quality Analysis

**Script:** `scripts/check_code_quality.sh`

**Purpose:** Identify code quality issues beyond metrics

**Checks:**
- TODOs and FIXMEs
- Print statements (should use logging)
- Bare except: clauses
- Long lines (>120 chars)
- High complexity functions

**Usage:** Run manually when needed
```bash
./scripts/check_code_quality.sh
```

**Status:** Available for manual runs. Removed from automated checks in v0.6.6 (no objective thresholds).

---

### Directory Organization

**Script:** `scripts/check_directory_organization.sh`

**Purpose:** Suggest organizational improvements

**Checks:**
- File placement (correct directories)
- Naming conventions
- Module structure
- Empty directories

**Usage:** Run manually when needed
```bash
./scripts/check_directory_organization.sh
```

**Status:** Available for manual runs. Removed from automated checks in v0.6.6 (subjective recommendations).

---

## Summary Table

| Check | Type | Execution Time | Status | Exit Codes | Blocks Release |
|-------|------|----------------|--------|------------|----------------|
| 1. Version Sync | Automated | ~1s | ✅ Working | 0=pass, 1=fail | Yes |
| 2. Code Complexity | Automated | ~2s | ✅ Working | 0=pass, 1=fail | Yes |
| 3. Client-Server Parity | Automated | ~1s | ✅ Working | 0=pass, 1=fail | Yes |
| 4. Milestone Status | Automated | ~1s | ✅ Working | 0=pass, 1=fail | Yes |
| 5. ROADMAP.md Sync | Automated | ~2s | ✅ Working | 0=pass, 1=fail | Yes |
| 6. Documentation Completeness | Automated | ~2s | ✅ Working | 0=pass, 1=fail | Yes |
| 7. Test Coverage | Automated | ~30s | ✅ Working | 0=pass, 1=fail | Yes |
| 8. All Tests | Automated | ~20-25 min | ✅ Working | 0=pass, 1=fail | Yes |
| Test Count Sync | Automated | ~5s | ✅ Working | 0=pass, 1=fail | No (not in pre-tag) |
| Doc Quality | Interactive | N/A | ⏳ To implement | N/A | No |
| Code Quality | Interactive | N/A | ✅ Available | N/A | No |
| Directory Org | Interactive | N/A | ✅ Available | N/A | No |

**Note:** Pre-tag hook runs 8 checks (1-8) in the order listed. Test Count Sync is available but not run automatically.

**Changes in v0.6.6:**
- Test Coverage promoted from interactive to automated (≥85% required)
- Code Quality and Directory Organization removed from automated checks (available for manual runs)
- ROADMAP.md Sync added as new automated check (#34)

**Changes in v0.6.7:**
- Documentation Completeness added as new automated check (#124)
- Verifies CHANGELOG entries, version references, migration guides, key docs existence

**Changes in v0.7.0:**
- Hygiene checks reordered for faster feedback (#132)
- Fast checks (1-6) run first, slow checks (7-8) run last
- Previous order had tests at position #2, now at position #8 (last)
- Prevents 20-25 minute wait when faster checks would have caught issues

---

## Notes

- **Automated checks** must have clear pass/fail criteria
- **Interactive checks** provide recommendations, not requirements
- **Exit codes** must reflect actual status (no `|| true` suppression)
- **Exceptions** must be documented (e.g., `get_tasks()` complexity)
- **Thresholds** chosen based on industry standards and project needs
