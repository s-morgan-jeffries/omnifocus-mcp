# Hygiene Check Pass/Fail Criteria

**Purpose:** Define clear, objective criteria for all automated hygiene checks.

**Last Updated:** 2025-10-30 (v0.6.6)

---

## Overview

Hygiene checks are split into two categories:

1. **Automated Checks** - Run on every RC tag, clear pass/fail, block release if fail
2. **Interactive Checks** - Run on-demand via slash commands, generate qualitative reports

This document defines the **automated check criteria** only. Interactive checks are documented in their respective slash command files.

---

## Automated Checks (Critical - Must Pass)

### 1. Version Synchronization

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

### 2. All Tests Pass

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

**Note:** GitHub Actions only runs unit tests (integration/E2E require local OmniFocus setup).

---

### 3. Code Complexity

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

### 4. Client-Server Parity

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

### 5. Test Count Synchronization

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

---

### 6. Milestone Status

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

### 7. ROADMAP.md Synchronization

**Script:** `scripts/check_roadmap_sync.sh` (**To be created** - issue #34)

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

**Status:** ⏳ Not yet implemented (part of v0.6.6, issue #34).

---

### 6. Test Coverage

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

### 7. ROADMAP.md Sync

**Script:** `scripts/check_roadmap_sync.sh`

**Pass Criteria:**
- ✅ All closed issues in milestone removed from active sections
- ✅ Active sections: "Upcoming Work", "Known Bugs", "Planned Work", etc.
- ✅ Issues can remain in "Completed" or be deleted entirely

**Fail Criteria:**
- ❌ One or more closed issues still in active sections

**Exit Codes:**
- `0` - All closed issues removed from active sections
- `1` - One or more closed issues found in active sections

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

| Check | Type | Status | Exit Codes | Blocks Release |
|-------|------|--------|------------|----------------|
| 1. Version Sync | Automated | ✅ Working | 0=pass, 1=fail | Yes |
| 2. All Tests | Automated | ✅ Working | 0=pass, 1=fail | Yes |
| 3. Code Complexity | Automated | ✅ Working | 0=pass, 1=fail | Yes |
| 4. Client-Server Parity | Automated | ✅ Working | 0=pass, 1=fail | Yes |
| 5. Milestone Status | Automated | ✅ Working | 0=pass, 1=fail | Yes |
| 6. Test Coverage | Automated | ✅ Working | 0=pass, 1=fail | Yes |
| 7. ROADMAP.md Sync | Automated | ✅ Working | 0=pass, 1=fail | Yes |
| Doc Quality | Interactive | ⏳ To implement | N/A | No |
| Code Quality | Interactive | ✅ Available | N/A | No |
| Directory Org | Interactive | ✅ Available | N/A | No |

**Changes in v0.6.6:**
- Test Coverage promoted from interactive to automated (≥85% required)
- Code Quality and Directory Organization removed from automated checks (available for manual runs)
- ROADMAP.md Sync added as new automated check (#34)
- Test Count Sync merged into Test Coverage check

---

## Notes

- **Automated checks** must have clear pass/fail criteria
- **Interactive checks** provide recommendations, not requirements
- **Exit codes** must reflect actual status (no `|| true` suppression)
- **Exceptions** must be documented (e.g., `get_tasks()` complexity)
- **Thresholds** chosen based on industry standards and project needs
