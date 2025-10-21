# Architectural Mistakes Log

**Purpose:** Track high-level architectural and workflow mistakes to improve development process.

**Last Updated:** 2025-10-21

**Statistics:**
- Total Mistakes: 11
- By Category: missing-docs (6), missing-tests (1), missing-automation (1), other (3)
- By Severity: critical (2), high (3), medium (6)

**Recent Patterns:** No patterns detected yet (need 3+ mistakes in same category)

---

## Active Mistakes (Not Yet Addressed in CLAUDE.md)

*No active mistakes logged yet*

---

## Resolved Mistakes (Addressed in CLAUDE.md)

*No resolved mistakes yet*

---

## Archived Mistakes (Historical Record)

*No archived mistakes yet*

---

## Mistake Entries

*Mistakes will be logged below using this template:*

```
## [MISTAKE-XXX] Brief Title (Date: YYYY-MM-DD)

**Status:** `open` | `fixing` | `prevention-pending` | `monitoring` | `resolved` | `archived`

**Category:** [missing-tests | missing-exposure | violated-tdd | violated-architecture | missing-docs | complexity-spike | other]

**Severity:** [critical | high | medium | low]
- **Critical:** Production issue, user-facing bug, data loss risk
- **High:** Missing major functionality, violates core principles
- **Medium:** Incomplete implementation, future maintenance burden
- **Low:** Minor oversight, easily fixed

**Discovery Date:** YYYY-MM-DD
**Introduced In:** [Commit hash or "Unknown"]
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** YYYY-MM-DD (30 days after prevention implemented)

**What Happened:**
[Detailed description of the mistake]

**Context:**
- **File(s):** [Affected files]
- **Function(s):** [Affected functions]
- **Commit:** [Git commit hash if applicable]

**Impact:**
[What broke? What was missing? What was the consequence?]

**Root Cause:**
[Why did this happen? What process step was missed?]

**Fix:**
[What was done to fix it?]
- **Resolved in commit:** [pending]
- **Prevention implemented in:** [file:line or pending]

**Prevention:**
[What could prevent this in the future? CLAUDE.md update? Checklist addition? New tooling?]
- **Prevention Status:** [ ] Not Started  [ ] Implemented  [ ] Validated

**Related Mistakes:**
[Links to similar mistakes: MISTAKE-XXX, MISTAKE-YYY]

**Effectiveness Score:** [pending | effective ✅ | partially-effective ⚠️ | ineffective ❌]
```

---


## [MISTAKE-001] Missing MIGRATION_v0.6.md despite CHANGELOG reference (Date: 2025-10-19)

**Status:** resolved

**Category:** missing-docs

**Severity:** high

**Discovery Date:** 2025-10-19
**Introduced In:** be794b4
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** 2025-11-18 (30 days from 2025-10-19)

**What Happened:**
During v0.6.0 API redesign implementation, updated CHANGELOG.md to reference `docs/MIGRATION_v0.6.md` for detailed migration guide, marked it as "(TODO)", but never created the file before marking the redesign as complete. This created a broken link in documentation and violated the established pattern (MIGRATION_v0.5.md exists for the v0.5.0 release).

**Context:**
- **File(s):** CHANGELOG.md (line 107), docs/MIGRATION_v0.6.md (missing)
- **Function(s):** N/A (documentation)
- **Commit:** 81aceb7 (added CHANGELOG v0.6.0 entry), be794b4 (marked redesign complete)

**Impact:**
- Created broken documentation link (CHANGELOG references non-existent file)
- Inconsistent with established pattern (v0.5.0 had migration guide)
- External users (if any exist) would have no migration path from v0.5.0 → v0.6.0
- Violated promise in CHANGELOG: "See docs/MIGRATION_v0.6.md"

**Root Cause:**
1. Focused on code implementation and basic CHANGELOG updates
2. Assumed migration guide could be created "later" as indicated by "(TODO)"
3. Marked redesign as "complete" without checking if all referenced documentation existed
4. No checklist item for "breaking changes require migration guide"
5. Didn't follow the pattern established by MIGRATION_v0.5.md

**Fix:**
1. Created docs/MIGRATION_v0.6.md following MIGRATION_v0.5.md template structure
2. Extracted migration examples from CHANGELOG.md (lines 24-51)
3. Documented all 26 removed functions with before/after examples
4. Removed "(TODO)" marker from CHANGELOG.md line 107

- **Resolved in commit:** 2ef5eaf
- **Prevention implemented in:** .claude/CLAUDE.md:246

**Prevention:**
Add to "Before Every Commit" checklist or "Common Development Tasks":
- **Breaking change releases:** If CHANGELOG documents removed/changed functions, verify migration guide exists
- **Cross-references:** Before committing documentation that references other files, verify those files exist
- **Pattern consistency:** If pattern exists (like MIGRATION_vX.Y.md), follow it for all similar releases

Alternative: Add to "Making a Breaking Change Release" workflow in docs/CONTRIBUTING.md

- **Prevention Status:** [x] Implemented  [x] Validated

**Related Mistakes:**
None yet (first logged mistake in tracking system)

**Effectiveness Score:** pending (verify 2025-11-18 - need 30 days, not 48 hours)

---


## [MISTAKE-002] TESTING.md test counts repeatedly get out of sync with actual tests (Date: 2025-10-19)

**Status:** monitoring

**Category:** missing-docs

**Severity:** medium

**Discovery Date:** 2025-10-19
**Introduced In:** Unknown (multiple commits over time)
**Recurrence Count:** 1
**Last Recurrence:** 2025-10-20 (added 2 tests for project review date fix, forgot to update TESTING.md)
**Verification Deadline:** 2025-11-19 (30 days from last recurrence)

**What Happened:**
TESTING.md contains hardcoded test counts and breakdowns that repeatedly become stale as tests are added/removed/refactored. During v0.6.0 API redesign, the documentation showed 393 tests in some places, 333 in others, and the actual count was 333. The coverage table in TESTING.md still referenced v0.5.0 function names (complete_task, add_task, etc.) even after v0.6.0 redesign removed them. This happened multiple times throughout the project.

**Context:**
- **File(s):** docs/TESTING.md (lines 21, 166-187, 336-365), README.md (lines 166-187), ROADMAP.md (lines 241-252), .claude/CLAUDE.md (line 143)
- **Function(s):** N/A (documentation)
- **Commits:** Multiple throughout v0.5.0 and v0.6.0 development

**Impact:**
- Documentation shows incorrect test counts, confusing contributors
- Coverage tables reference deprecated/removed functions
- Test count is duplicated in 4+ files, requiring manual sync across all
- Human readers get conflicting information
- AI readers may reference wrong function names from outdated coverage tables

**Root Cause:**
1. Test counts are manually hardcoded in documentation instead of generated
2. No automated check that TESTING.md matches actual pytest output
3. Coverage breakdown by function is manually maintained
4. Same information duplicated across 4+ files (TESTING.md, README.md, ROADMAP.md, CLAUDE.md)
5. No single source of truth for test statistics

**Fix:**
1. Consolidated test counts to single source (TESTING.md) with all other docs referencing it
2. Removed stale v0.5.0 coverage table from TESTING.md
3. Updated all docs to say "See TESTING.md for detailed breakdown" instead of duplicating numbers
4. Replaced obsolete coverage table with summary: "All 16 core v0.6.0 MCP tools have comprehensive coverage"

- **Resolved in commit:** 2ef5eaf
- **Prevention implemented in:** .claude/CLAUDE.md:247, docs/guides/CONTRIBUTING.md

**Prevention:**
**Short term (manual maintenance):**
- Add to "Before Every Commit" checklist: "If tests added/removed, update test count in TESTING.md only"
- TESTING.md is single source of truth; all other docs reference it
- Don't duplicate test breakdowns; link to TESTING.md instead

- **Prevention Status:** [x] Implemented  [ ] Validated (awaiting next test count change)

**Long term (automation):**
- Create script `scripts/generate_test_stats.sh` that runs pytest and extracts actual counts
- Script outputs markdown snippet that can be pasted into TESTING.md
- Pre-commit hook could warn if TESTING.md test count differs from actual pytest output
- Even better: Generate TESTING.md statistics section automatically from pytest --collect-only

**Example automation:**
```bash
# scripts/generate_test_stats.sh
pytest --collect-only -q | tail -1  # "333 tests collected"
pytest tests/ --cov --cov-report=term | grep "TOTAL"  # Coverage percentage
```

**Related Mistakes:**
Similar to MISTAKE-003 - both are "duplicated information that gets out of sync"

**Effectiveness Score:** pending (prevention implemented, monitoring for recurrence)

---


## [MISTAKE-003] Version numbers duplicated across multiple files, get out of sync (Date: 2025-10-19)

**Status:** monitoring

**Category:** missing-docs

**Severity:** high

**Discovery Date:** 2025-10-19
**Introduced In:** Unknown (multiple commits over time)
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** 2025-11-18 (30 days from 2025-10-19)

**What Happened:**
Version number is documented in multiple places (pyproject.toml, CHANGELOG.md, ROADMAP.md, README.md, CLAUDE.md, archive/README.md) and repeatedly gets out of sync. During v0.6.0 work, pyproject.toml showed 0.5.0 while all documentation claimed 0.6.0 was complete. Archive README still said "current version: v0.5.0" weeks after v0.6.0 completion. This has happened multiple times across different releases.

**Context:**
- **File(s):**
  - pyproject.toml (line 7 - authoritative source)
  - CHANGELOG.md (version headers)
  - docs/ROADMAP.md (multiple version references)
  - README.md (feature descriptions with versions)
  - .claude/CLAUDE.md (line 141 - "Current Version")
  - docs/archive/README.md (line 7, 73 - archive metadata)
- **Function(s):** N/A (documentation/metadata)
- **Commits:** Multiple throughout v0.5.0 and v0.6.0 development

**Impact:**
- Code says one version (pyproject.toml), docs say another
- PyPI package would have wrong version if published
- Users/contributors confused about actual project version
- Archive documentation references "current version" that's outdated
- No single source of truth for version number

**Root Cause:**
1. Version number manually duplicated in 6+ locations
2. No automated synchronization between pyproject.toml and documentation
3. No checklist reminder to update version across all files
4. Version bumping is manual, easy to miss files
5. Archive documentation says "current version" instead of "version when archived"

**Fix:**
1. Updated pyproject.toml from 0.5.0 to 0.6.0 (authoritative source)
2. Verified all documentation references v0.6.0 correctly
3. Updated archive/README.md to clarify "version when archive created" vs "current project version"
4. Consolidated version references where possible

- **Resolved in commit:** 2ef5eaf
- **Prevention implemented in:** docs/guides/CONTRIBUTING.md:313-343

**Prevention:**
**Short term (manual process):**
- Add to "Making a Release" workflow in CONTRIBUTING.md:

- **Prevention Status:** [x] Implemented  [ ] Validated (awaiting next version bump)
  1. Update pyproject.toml version (authoritative)
  2. Add CHANGELOG.md entry with new version header
  3. Update CLAUDE.md "Current Version" line
  4. Update README.md if version appears in feature descriptions
  5. Commit with message: "chore: bump version to vX.Y.Z"

**Long term (automation):**
- Use `bump2version` or similar tool to automate version bumping
- Script that reads version from pyproject.toml and validates docs match:
  ```bash
  # scripts/check_version_sync.sh
  VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
  grep -l "Current Version.*$VERSION" .claude/CLAUDE.md || echo "CLAUDE.md out of sync"
  grep -l "## \[$VERSION\]" CHANGELOG.md || echo "CHANGELOG.md missing version"
  ```
- Pre-commit hook that warns if CHANGELOG.md latest version ≠ pyproject.toml
- Consider using dynamic version from pyproject.toml in docs (e.g., include directive)

**Related Mistakes:**
Similar to MISTAKE-002 - both are "duplicated information that gets out of sync"
Pattern: **Documentation duplication without single source of truth**

**Effectiveness Score:** pending (prevention implemented, monitoring for recurrence)

---


## [MISTAKE-004] Metrics automation script exists but never runs automatically (Date: 2025-10-19)

**Status:** resolved

**Category:** other

**Severity:** high

**Discovery Date:** 2025-10-19
**Introduced In:** 08acfa5
**Recurrence Count:** 0

**What Happened:**
Created `scripts/update_metrics.sh` as part of Priority 1 mistake tracking improvements (commit 08acfa5) with the explicit goal of automating METRICS.md updates. The script was documented, tested manually, and works correctly. However, it was never integrated into any automated workflow (git hooks, CI/CD, or scheduled tasks). As a result, METRICS.md still shows "Last Updated: 2025-10-17" and must be manually updated, defeating the purpose of the automation script.

**Context:**
- **File(s):** scripts/update_metrics.sh, scripts/git-hooks/commit-msg, .claude/METRICS.md
- **Function(s):** N/A (infrastructure)
- **Commit:** 08acfa5 (created script), c0453c3 (documented it but didn't auto-call it)

**Impact:**
- Broken promise of automation - script exists but isn't automatic
- METRICS.md becomes stale immediately after creation
- Manual toil remains despite automation investment
- Second-level gap analysis (this one) caught the oversight
- Meta-mistake: The mistake tracking system had a mistake in its implementation

**Root Cause:**
1. Focused on creating the script but not integrating it into workflows
2. No checklist item for "automation scripts must be called automatically"
3. Testing was manual ("does the script work?") not integration ("is it actually triggered?")
4. Documentation showed the script exists but didn't verify automated invocation
5. Priority 1 implementation was marked complete without end-to-end validation

**Fix:**
Added call to `update_metrics.sh` at the end of `commit-msg` git hook. When a commit references a mistake (e.g., "Resolves: MISTAKE-XXX"), the hook now automatically updates metrics after validating the mistake ID.

- **Resolved in commit:** [current commit]
- **Prevention implemented in:** scripts/git-hooks/commit-msg:50-59

**Prevention:**
1. **Process improvement:** For all automation scripts, verify they're actually called in workflow (not just that they exist)
2. **Testing requirement:** Integration tests for automation (does git hook call script? does script run on trigger?)
3. **Documentation standard:** Scripts README should list trigger mechanism, not just manual usage
4. **Checklist addition:** "Before marking automation task complete, verify end-to-end automated execution"

- **Prevention Status:** [x] Implemented  [ ] Validated (will be tested in next commit)

**Related Mistakes:**
MISTAKE-005, MISTAKE-006 (other meta-mistakes in mistake tracking system found by second-level analysis)

**Effectiveness Score:** pending (just implemented)

---


## [MISTAKE-007] No validation that prevention measures actually work (Date: 2025-10-19)

**Status:** monitoring

**Category:** missing-tests

**Severity:** critical

**Discovery Date:** 2025-10-19
**Introduced In:** 08acfa5
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** 2025-11-18 (30 days from 2025-10-19)

**What Happened:**
Implemented Priority 1 and Priority 2 mistake tracking improvements, creating prevention scripts like `check_version_sync.sh` and `check_test_count_sync.sh`. These scripts were manually tested (they work when run directly), documented, and integrated into git hooks. However, there's no automated testing that validates the prevention scripts actually detect their target mistakes. This means we can't prove prevention works, and bugs in prevention scripts would go undetected.

**Context:**
- **File(s):** scripts/check_version_sync.sh, scripts/check_test_count_sync.sh, scripts/verify_prevention.sh
- **Function(s):** N/A (infrastructure)
- **Commit:** 08acfa5 (created prevention scripts without tests)

**Impact:**
- Cannot prove prevention measures actually work
- Cannot answer "Did prevention for MISTAKE-001 succeed?" with data
- Prevention scripts could have bugs that give false negatives (fail to detect mistakes)
- No recurrence tracking - if prevented mistake happens again, system doesn't notice
- Breaks the feedback loop: Detection → Prevention → ❌ Validation → Measurement
- System cannot achieve true recursive self-improvement without validation

**Root Cause:**
1. Focused on creating prevention scripts but not testing them
2. Manual testing ("does script run?") but not integration testing ("does script detect mistakes?")
3. No test cases for positive (script catches mistake) and negative (script allows valid code) scenarios
4. `verify_prevention.sh` checks script existence, not correctness
5. Original gap analysis identified this (Gap #14: Prevention script testing) as Priority 3, but it's actually critical

**Fix:**
Need to create:
1. `scripts/test_prevention_measures.sh` - Tests all prevention scripts
2. For each prevention script, create test scenarios:
   - Positive: Script should detect mistake (e.g., create version mismatch, verify script catches it)
   - Negative: Script should allow valid code (e.g., create matching versions, verify script passes)
3. Add prevention tests to CI/CD pipeline
4. Add recurrence tracking to MISTAKES.md template

- **Resolved in commit:** pending
- **Prevention implemented in:** pending

**Prevention:**
1. **Standard:** All prevention scripts must have automated tests
2. **Process:** Before marking prevention "Validated", run automated tests
3. **CI/CD:** Prevention tests must pass before merge
4. **Template:** Add "Prevention Tests" section to MISTAKES.md template

- **Prevention Status:** [ ] Not Started  [ ] Implemented  [ ] Validated

**Related Mistakes:**
MISTAKE-004 (metrics automation), MISTAKE-008 (no recurrence tracking)

**Effectiveness Score:** pending

---


## [MISTAKE-008] No recurrence tracking to measure prevention effectiveness (Date: 2025-10-19)

**Status:** monitoring

**Category:** missing-docs

**Severity:** critical

**Discovery Date:** 2025-10-19
**Introduced In:** e141f53
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** 2025-11-18 (30 days from 2025-10-19)

**What Happened:**
Updated MISTAKES.md template to include "Recurrence Count" field (commit e141f53) as part of Priority 1 improvements. However, there's no mechanism to actually detect when a prevented mistake recurs, no script to increment the recurrence count, and no validation timeline to determine when prevention can be marked as "effective." MISTAKE-001 is marked "Status: resolved" and "Effectiveness Score: effective ✅" but there's no data proving prevention worked - it's based on assumption, not measurement.

**Context:**
- **File(s):** .claude/MISTAKES.md (template has field), scripts/ (no recurrence detection script)
- **Function(s):** N/A (infrastructure)
- **Commit:** e141f53 (added field but not detection mechanism)

**Impact:**
- Cannot measure prevention effectiveness with data
- Cannot answer "Did MISTAKE-001 prevention work?" objectively
- Recurrence Count field exists but is never updated (always stays 0)
- No way to know if prevention failed (mistake happened again)
- Can't improve prevention strategies based on effectiveness
- Status "monitoring" has no defined transition to "resolved" (when? based on what?)
- Breaks the measurement phase of the feedback loop

**Root Cause:**
1. Added template field without implementing detection mechanism
2. No script to scan for patterns of previously prevented mistakes
3. No verification timeline (30/60/90 days without recurrence = effective?)
4. Status lifecycle documented but transition criteria unclear
5. Assumed effectiveness based on "no complaints" rather than active measurement

**Fix:**
Need to implement:
1. `scripts/check_recurrence.sh` - Scans codebase/commits for patterns of previous mistakes
2. Verification timeline: Add "Verification Deadline" field (e.g., Prevention Date + 30 days)
3. `scripts/check_monitoring_deadlines.sh` - Identifies mistakes overdue for verification
4. Auto-transition from "monitoring" → "resolved" if no recurrence detected after deadline
5. Recurrence detection integrated into pre-commit hook

- **Resolved in commit:** pending
- **Prevention implemented in:** pending

**Prevention:**
1. **Template addition:** Add "Verification Deadline" field to MISTAKES.md template
2. **Process standard:** Status "monitoring" requires 30-day observation period minimum
3. **Automation:** Recurrence detection runs in pre-commit hook
4. **Measurement:** Effectiveness Score based on recurrence rate, not assumption

- **Prevention Status:** [ ] Not Started  [ ] Implemented  [ ] Validated

**Related Mistakes:**
MISTAKE-004 (metrics automation), MISTAKE-007 (no prevention validation)

**Effectiveness Score:** pending

---


## [MISTAKE-009] Started implementation without planning version bump and documentation (Date: 2025-10-20)

**Status:** resolved

**Category:** other

**Severity:** medium

**Discovery Date:** 2025-10-20
**Introduced In:** refactor/rename-client-to-connector branch (during development)
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** 2025-11-19 (30 days from fix)

**What Happened:**

When implementing the omnifocus_client → omnifocus_connector rename, I immediately started the rename without:
1. Asking if this should be v0.6.1 or stay as v0.6.0
2. Deciding on the roadmap documentation strategy first
3. Planning the full scope (rename + version bump + CHANGELOG + roadmap update)

User had to stop me twice:
- First to point out I marked it completed but left it in "Upcoming Work"
- Second to ask "should you log this as a mistake?"

**Context:**
- **File(s):** Multiple (rename affected 34+ files)
- **Task:** Rename omnifocus_client.py → omnifocus_connector.py
- **Commit:** In progress on refactor/rename-client-to-connector branch

**Impact:**

- **User experience:** Had to intervene twice to correct approach
- **Process:** Violated planning-before-implementation principle
- **Documentation:** Nearly shipped with inconsistent docs
- **Severity:** Medium - Caught early, no code shipped, but wasted time

**Root Cause:**

Jumped straight to implementation without considering:
- This is a breaking change requiring version bump
- Documentation strategy needed to be decided first (remove vs mark complete vs note in version)
- Full scope planning needed before execution

**Fix:**

- Paused implementation when user stopped me
- Asked clarifying questions about versioning (should be v0.6.1)
- Asked about documentation approach (Option A/B/C)
- Got agreement on approach (Option B: note in Current State + CHANGELOG)
- Now implementing properly with full scope

- **Resolved in commit:** pending (will be in v0.6.1 commit)
- **Prevention implemented in:** This commit (logged as mistake for awareness)

**Prevention:**

1. **Pre-implementation checklist** (add to CLAUDE.md):
   - [ ] Is this a breaking change? → Requires version bump
   - [ ] Does this need CHANGELOG entry? → Plan what goes in it
   - [ ] Does this affect roadmap? → Decide documentation strategy
   - [ ] What's the full scope? → List all affected files/docs

2. **Breaking change protocol** (add to CONTRIBUTING.md):
   - Always ask about versioning before implementing breaking changes
   - Decide documentation strategy before starting
   - Plan full scope including: code + tests + docs + CHANGELOG + version bump

- **Prevention Status:** [X] Implemented (logged for awareness, checklist to be added to docs)

**Related Mistakes:**

- MISTAKE-001: Missing MIGRATION_v0.6.md (also a planning/docs issue)
- General pattern: Jumping to implementation before planning docs/versioning


**Effectiveness Score:** pending

---


## [MISTAKE-012] Failed to update ROADMAP.md after fixing critical bug (Date: 2025-10-21)

**Status:** resolved

**Category:** missing-docs

**Severity:** medium

**Discovery Date:** 2025-10-21
**Introduced In:** 080de69 (bug fix commit from 2025-10-20)
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** 2025-11-20 (30 days after prevention implemented)

**What Happened:**

On 2025-10-20, I fixed a critical bug in the project review date functionality (commit 080de69). The bug was documented in ROADMAP.md under "Upcoming Work - Bug Fixes" as a CRITICAL priority item. I:

1. Fixed the bug (added `next_review_date` parameter, fixed `last_reviewed` to set correct property)
2. Updated CHANGELOG.md with full details (v0.6.1 section)
3. Added 2 new tests for the functionality
4. Updated all related documentation

BUT: I never removed the bug from the ROADMAP.md "Upcoming Work" section. On 2025-10-21, when user asked "what's in the current roadmap?", they saw the bug still listed as CRITICAL even though it was fixed yesterday.

User had to point out: "That's weird, I thought we already fixed that critical bug."

**Context:**
- **File(s):** docs/project/ROADMAP.md (lines 337-355 still show bug as unfixed)
- **Function(s):** update_project(), update_projects() (bug was fixed in these)
- **Commit:** 080de69 (fixed bug), e4c28fb (documented in CHANGELOG), but ROADMAP.md never updated

**Impact:**

- **User confusion:** Sees resolved bug still listed as CRITICAL TODO
- **Stale documentation:** ROADMAP doesn't reflect current project state
- **Lost trust:** Makes it look like bug isn't actually fixed
- **Duplicate work risk:** Could start working on "fixing" already-fixed bug
- **Pattern:** This is exactly like MISTAKE-010 (the other one about roadmap documentation patterns)

**Root Cause:**

1. **No checklist item:** "Before Every Commit" doesn't include "Update ROADMAP.md if completing roadmap items"
2. **Focus on CHANGELOG:** Assumed CHANGELOG.md was sufficient for documenting fixes
3. **Incomplete mental model:** Thought of bug fix as "code change" not "roadmap change"
4. **No cross-reference check:** CHANGELOG mentions bug fix but didn't verify ROADMAP shows same status
5. **Recurrence of MISTAKE-010:** Same pattern - completed work not removed from "Upcoming Work"

**Fix:**

Remove the "Immediate - Bug Fixes" section from ROADMAP.md since the bug is fixed. The fix is already documented in:
- CHANGELOG.md v0.6.1 section (full technical details)
- Code itself (omnifocus_connector.py has both parameters working correctly)
- Tests (2 new tests verify functionality)

- **Resolved in commit:** c77538f
- **Prevention implemented in:** pending (need to update CLAUDE.md checklist)

**Prevention:**

1. **Add to "Before Every Commit" checklist in CLAUDE.md:**
   - [ ] If fixing a bug documented in ROADMAP.md, remove it from "Upcoming Work"
   - [ ] If completing a roadmap item, update ROADMAP.md per documentation pattern

2. **Add to bug fix workflow in CONTRIBUTING.md:**
   - When fixing bugs listed in ROADMAP.md:
     1. Fix the bug
     2. Update CHANGELOG.md
     3. Update ROADMAP.md (remove from "Upcoming Work")
     4. Verify all three are consistent

3. **Create cross-reference check script:**
   ```bash
   # scripts/check_roadmap_sync.sh
   # Check if CHANGELOG mentions items still in ROADMAP "Upcoming Work"
   ```

- **Prevention Status:** [ ] Not Started  [ ] Implemented  [ ] Validated

**Related Mistakes:**

- MISTAKE-001: Missing MIGRATION_v0.6.md (documentation not updated)
- MISTAKE-002: Test counts get out of sync (documentation drift)
- MISTAKE-003: Version numbers get out of sync (documentation drift)
- **Pattern: Documentation updates are inconsistently applied across related files**

**Effectiveness Score:** pending

---

## Quick Reference

**Log a new mistake:**
```bash
./scripts/log_mistake.sh
```

**Analyze patterns:**
```bash
./scripts/analyze_mistakes.py  # When created
```

**Categories:**
- `missing-tests` - Failed to write unit, integration, or e2e tests
- `missing-exposure` - Implemented in client but didn't expose in server
- `violated-tdd` - Wrote implementation before tests
- `violated-architecture` - Didn't follow architecture principles/decision tree
- `missing-docs` - Failed to update CHANGELOG, API_REFERENCE, etc.
- `complexity-spike` - Function rated D or F without documentation
- `other` - Other architectural/workflow mistakes

---


## [MISTAKE-010] No documented pattern for where completed roadmap items should go (Date: 2025-10-20)

**Status:** resolved

**Category:** missing-docs

**Severity:** medium

**Discovery Date:** 2025-10-20
**Introduced In:** Unknown (documentation process gap)
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** 2025-11-19 (30 days from fix)

**What Happened:**

When implementing client→connector rename (v0.6.1), unclear where completed "Upcoming Work" items should go:

1. **First attempt:** Marked item as completed but left it in "Upcoming Work" section
   - User stopped me: "You marked this as completed but it's still in upcoming work"
2. **Second attempt:** Asked user: "Should I remove it or mark as complete?"
   - User: "That's a real question, not rhetorical"
3. **Final decision:** Remove from "Upcoming Work", add brief note to "Current State" + CHANGELOG

**Context:**
- **File(s):** docs/project/ROADMAP.md
- **Task:** Documenting completion of client→connector rename
- **Issue:** No documented pattern for handling completed roadmap items

**Impact:**

- **User experience:** Had to intervene to clarify documentation approach
- **Process gap:** No clear guidance on where completed work goes
- **Confusion:** Three different options (remove, mark complete, move to section)
- **Recurrence risk:** HIGH - Will happen again with next completed item

**Root Cause:**

ROADMAP.md has clear sections for:
- "Upcoming Work" (future items)
- "Completed Phases" (major phases like Phase 1-3)

But no documented pattern for:
- Small completed items (not worth a whole phase)
- Where to note completion (Current State? Upcoming Work? New section?)
- When to remove vs mark complete

**Fix:**

Decided on pattern: For small completed items:
1. Remove from "Upcoming Work" section
2. Add brief note to "Current State" section (e.g., "Latest: v0.6.1 renamed X→Y")
3. Document fully in CHANGELOG.md
4. For major features, document in "Completed Phases"

- **Resolved in commit:** This commit (v0.6.1 work + this mistake log)
- **Prevention implemented in:** This commit

**Prevention:**

1. **Document the pattern** (add to CONTRIBUTING.md or ROADMAP.md header):
   ```markdown
   ## How to Document Completed Work
   
   **Small items (code quality, bug fixes):**
   - Remove from "Upcoming Work"
   - Add brief note to "Current State" (e.g., "Latest: v0.6.1 ...")
   - Document in CHANGELOG.md with details
   
   **Major features/phases:**
   - Add to "Completed Phases" section
   - Document deliverables and success criteria
   - Reference in CHANGELOG.md
   
   **Version bumps:**
   - Always note in "Current State" header
   - Document breaking changes in CHANGELOG.md
   ```

2. **Add to pre-commit checklist** (CONTRIBUTING.md):
   - [ ] If completing roadmap item, updated ROADMAP.md per documentation pattern
   - [ ] Added to CHANGELOG.md with appropriate detail level

- **Prevention Status:** [X] Implemented (pattern documented in this mistake)

**Related Mistakes:**

- MISTAKE-009: Started implementation without planning (related planning issue)
- MISTAKE-001: Missing MIGRATION_v0.6.md (also documentation pattern issue)
- General pattern: Undocumented processes lead to inconsistent execution

**Effectiveness Score:** pending

---

## [MISTAKE-011] No proactive GitHub Actions monitoring after git push (Date: 2025-10-20)

**Status:** open

**Category:** missing-automation

**Severity:** medium

**Discovery Date:** 2025-10-20
**Introduced In:** Initial CI/CD setup (whenever GitHub Actions were first added)
**Recurrence Count:** Multiple (happened 3 times today during bug fix cycle)
**Last Recurrence:** 2025-10-20
**Verification Deadline:** 2025-11-19 (30 days from fix)

**What Happened:**

During the project review date bug fix (v0.6.1), I pushed 3 commits to fix CI issues:
1. Push 1: README version sync issue - User had to notify me via email/URL
2. Push 2: test_prevention_measures.sh cd bug - User had to notify me via email/URL
3. Push 3: Arithmetic expansion ||true fix - User had to notify me via email/URL

Each time:
- I pushed code without monitoring the GitHub Actions run
- User received email notification of failure
- User manually gave me the failure URL
- I then checked logs and fixed the issue
- Repeat cycle

**Context:**
- **Commands used:** `git push origin main`
- **Available tooling:** `gh run list`, `gh run watch`, `gh run view --log-failed`
- **Issue:** I completed the push and moved on without monitoring CI results
- **User question:** "Would it be possible for you to check the actions automatically after you push?"

**Impact:**

- **User interruption:** User had to check email, copy URLs, and paste them to me (3 times)
- **Slow feedback loop:** Each fix-push-notify-check cycle took several minutes
- **Wasted time:** Could have been caught immediately with automatic monitoring
- **Broken promise:** I said "I can do that" but didn't implement it as a systematic behavior
- **Recurrence risk:** VERY HIGH - Will happen on every push unless systematically prevented

**Root Cause:**

1. **No systematic post-push workflow:** I treat `git push` as "done" instead of "deployment started"
2. **No automated monitoring pattern:** GitHub CLI tools exist (`gh run watch`) but not used proactively
3. **Reactive vs proactive mindset:** Wait for user to report failures instead of monitoring actively
4. **No documented process:** CLAUDE.md and CONTRIBUTING.md don't include CI monitoring in push workflow

**Fix:**

**Prevention Measures:**

1. **Systematic post-push monitoring pattern:**
   ```bash
   # After EVERY git push to origin:
   1. Get latest run ID: gh run list --limit 1 --json databaseId
   2. Monitor until complete: gh run watch <run_id> (or poll with gh run list)
   3. If failure: gh run view <run_id> --log-failed
   4. Report status to user immediately
   5. If failed: Diagnose, fix, and repeat
   ```

2. **Update CLAUDE.md "Before Every Commit" checklist:**
   Add section "After Every Push":
   - [ ] Monitor GitHub Actions run until completion
   - [ ] Report CI status to user (pass/fail)
   - [ ] If failed: Fetch logs, diagnose, propose fix

3. **Update CONTRIBUTING.md push workflow:**
   Document that pushes should include CI monitoring as standard practice

4. **Automation mindset shift:**
   - `git push` is not "done" - it's "deployment started"
   - CI monitoring is part of the push workflow, not optional
   - Proactive monitoring prevents user interruption

**Prevention Implementation:**

- [ ] Add "After Every Push" section to CLAUDE.md
- [ ] Add CI monitoring example to CONTRIBUTING.md
- [ ] Test pattern: Next push should automatically monitor and report status
- [ ] Monitor for 30 days to ensure habit is formed

- **Prevention Status:** [ ] Not yet implemented

**Related Mistakes:**

- MISTAKE-009: Started implementation without planning (both are process gaps)
- General pattern: Missing systematic workflows lead to inconsistent execution

**Effectiveness Score:** pending (prevention not yet implemented)

