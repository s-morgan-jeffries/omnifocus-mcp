# Release Process

**Version:** v0.6.6+
**Last Updated:** 2025-11-01

This document defines the complete release process for the OmniFocus MCP Server, including automated checks, interactive quality reviews, and enforcement mechanisms.

---

## Release Types

### Patch Releases (v0.6.x)

**Purpose:** Bug fixes, documentation updates, minor improvements

**Quality Gates:** Automated checks only (pass/fail criteria)

**Process:**
1. Create release branch: `release/v0.6.x`
2. Tag RC: `git tag v0.6.x-rc1`
3. Pre-tag hook runs 7 automated checks (must pass)
4. Fix any failures, tag new RC if needed
5. Merge to main, tag final: `git tag v0.6.x`

**Automated Checks (7 critical):**
1. Version synchronization
2. All tests pass (unit + integration + e2e)
3. Code complexity thresholds
4. Client-server parity
5. Milestone status (all issues closed)
6. Test coverage ≥ 85%
7. ROADMAP.md sync (closed issues removed)

### Minor Releases (v0.x.0)

**Purpose:** New features, API changes, significant improvements

**Quality Gates:** Automated checks + interactive quality reviews

**Process:**
1. Create release branch: `release/v0.x.0`
2. **Run interactive quality checks** (before RC tag)
3. Review results and address issues
4. Tag RC: `git tag v0.x.0-rc1`
5. Pre-tag hook runs automated checks + prompts for quality review confirmation
6. Fix any failures, tag new RC if needed
7. Merge to main, tag final: `git tag v0.x.0`

**Interactive Quality Checks (4 required):**
1. `/doc-quality` - Documentation quality assessment
2. `/code-quality` - Code quality beyond complexity
3. `/test-coverage` - Test coverage beyond 85% threshold
4. `/directory-check` - Directory organization assessment

**See:** "Minor Release Interactive Checks" section below for details

### Major Releases (vX.0.0)

**Purpose:** Breaking changes, major architectural changes

**Quality Gates:** Automated checks + interactive quality reviews + manual review

**Process:** Same as minor releases, plus:
- External review of breaking changes
- Migration guide completion
- Backwards compatibility assessment
- User communication plan

---

## Minor Release Interactive Checks

### When to Run

Run all four interactive quality checks **before creating the first RC tag** for a minor release.

**Recommended timing:**
```bash
# 1. Feature development complete, all issues closed
# 2. Run interactive checks
/doc-quality
/code-quality
/test-coverage
/directory-check

# 3. Review results and address critical issues
# 4. Create RC tag
git tag v0.x.0-rc1
```

### What Each Check Provides

#### `/doc-quality` - Documentation Quality

**Checks:**
- README completeness and accuracy
- Foundation model interpretability
- Cross-reference integrity
- Technical accuracy (code examples match API)
- Clarity, consistency, and completeness

**Look for:**
- Critical: Outdated examples, broken links, incorrect version references
- Recommended: Missing edge case docs, unclear explanations
- Minor: Formatting improvements, typos

#### `/code-quality` - Code Quality

**Checks:**
- Cyclomatic complexity (D-F rated functions)
- TODO/FIXME markers and technical debt
- print() statements vs logging
- Bare except clauses
- Line length and readability

**Look for:**
- Critical: D-F complexity without documentation, bare except in prod code
- Recommended: Old TODOs without tracking issues, print() in library code
- Minor: Minor readability improvements, acceptable long lines

#### `/test-coverage` - Test Coverage

**Checks:**
- Coverage metrics vs 85% threshold
- TODO test markers
- Untested public functions
- Coverage gaps by module
- Test quality (edge cases, mocking)
- Testing types assessment

**Look for:**
- Critical: Coverage below 85%, critical functions untested
- Recommended: Missing edge case tests, beneficial testing types
- Minor: Test quality improvements, nice-to-have coverage

#### `/directory-check` - Directory Organization

**Checks:**
- Directory structure logic
- File organization and placement
- Documentation structure
- Archive organization
- Configuration file placement
- New contributor clarity

**Look for:**
- Critical: Misplaced critical files, confusing structure
- Recommended: Missing READMEs, archive candidates
- Minor: Organizational improvements, future-proofing

### Enforcement Mechanism

The pre-tag hook for minor release RC tags **prompts the developer to confirm** they have run and reviewed the interactive quality checks.

**Example prompt:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Minor Release Detected: v0.7.0-rc1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Minor releases require interactive quality checks.

Required before tagging:
  ✓ /doc-quality - Documentation quality assessment
  ✓ /code-quality - Code quality review
  ✓ /test-coverage - Test coverage analysis
  ✓ /directory-check - Directory organization check

Have you run all four interactive quality checks? (y/n)
```

**If yes:** Hook continues with automated checks
**If no:** Hook exits with instructions to run checks first

This creates accountability without being overly restrictive.

---

## Converting Interactive Checks to Automated Checks

### Criteria for Automation

An interactive quality check should be converted to an automated check when it meets ALL of the following criteria:

#### 1. Clear Pass/Fail Criteria

**Required:** The check must have objective, deterministic criteria that can be automated.

**Examples:**
- ✅ "Coverage must be ≥ 85%" - Clear threshold
- ✅ "No bare except: clauses in src/" - Binary check
- ❌ "Documentation should be clear" - Subjective
- ❌ "Code organization is intuitive" - Subjective

#### 2. Consistent Failures

**Required:** The check has failed in at least **3 consecutive releases** OR has caused **2+ post-release issues**.

**Examples:**
- ✅ Coverage dropped below 85% in v0.6.3, v0.6.4, v0.6.5 → Automate
- ✅ Outdated docs caused 2 user-reported issues → Automate link checking
- ❌ Directory check never found issues → Keep interactive

#### 3. High Impact

**Required:** Failures in this check cause one of:
- User-facing bugs or confusion
- Significant contributor friction
- Post-release hotfixes
- Security vulnerabilities

**Examples:**
- ✅ Outdated API examples cause user confusion → Automate
- ✅ Missing tests led to production bug → Automate
- ❌ Minor TODO comments don't impact users → Keep interactive

#### 4. Low False Positive Rate

**Required:** Automated check must not block releases for acceptable cases.

**Examples:**
- ✅ "No bare except in src/" - Rarely acceptable
- ✅ "Coverage ≥ 85%" - Clear threshold with approval workflow
- ❌ "No lines > 120 chars" - Many acceptable cases (data, logging)
- ❌ "No TODO comments" - TODOs with tracking issues are acceptable

#### 5. Maintainable Automation

**Required:** The check can be implemented as a bash script that:
- Runs in < 30 seconds
- Has clear pass/fail exit codes
- Provides actionable error messages
- Doesn't require manual review

**Examples:**
- ✅ grep + wc for counting issues → Simple script
- ✅ pytest --cov for coverage → Existing tool
- ❌ "Is documentation clear?" → Requires human judgment
- ❌ "Are design decisions well-justified?" → Requires human judgment

### Automation Decision Process

When considering automation:

1. **Identify the issue** - What specific failure occurred?
2. **Extract the criteria** - What objective rule would catch this?
3. **Check recurrence** - Has this happened multiple times?
4. **Assess impact** - Does this justify blocking releases?
5. **Prototype the check** - Can it be scripted reliably?
6. **Test false positives** - Run on last 5 releases - any false blocks?
7. **Decide** - If all 5 criteria met, automate. Otherwise, keep interactive.

### Examples of Automation Decisions

#### Example 1: Bare except: Clauses

**Issue:** Found bare except: clauses in production code during `/code-quality` review

**Criteria:**
- ✅ Clear pass/fail: `grep -r "except:" src/ | grep -v "# except: OK"`
- ✅ Consistent failures: Found in v0.6.3, v0.6.4, v0.6.5
- ✅ High impact: Could mask errors, caused bug in v0.6.4
- ✅ Low false positives: Rarely acceptable in production
- ✅ Maintainable: Simple grep script

**Decision:** AUTOMATE - Add to check_code_quality.sh as blocking check

#### Example 2: Documentation Clarity

**Issue:** Documentation unclear during `/doc-quality` review

**Criteria:**
- ❌ Clear pass/fail: "Clarity" is subjective
- ✅ Consistent failures: Reported in multiple releases
- ✅ High impact: User confusion reported
- ❌ Low false positives: N/A (can't automate subjectively)
- ❌ Maintainable: Requires human judgment

**Decision:** KEEP INTERACTIVE - Cannot be objectively automated

#### Example 3: Outdated Version References

**Issue:** Found "v0.6.2" references in docs during v0.6.5 release

**Criteria:**
- ✅ Clear pass/fail: `grep -r "v0\.6\." docs/ | grep -v "$(cat VERSION)"`
- ⚠️ Consistent failures: Happened once in v0.6.5
- ⚠️ High impact: Confusing but not breaking
- ✅ Low false positives: Old versions in CHANGELOG are acceptable (with filtering)
- ✅ Maintainable: Simple grep script

**Decision:** WATCH - Add to tracking list. If happens again, automate with exclusions for CHANGELOG.

#### Example 4: Missing Directory READMEs

**Issue:** `/directory-check` suggested adding scripts/README.md

**Criteria:**
- ✅ Clear pass/fail: `[ -f scripts/README.md ]`
- ❌ Consistent failures: First occurrence
- ❌ High impact: Minor contributor friction
- ✅ Low false positives: Simple file existence check
- ✅ Maintainable: Trivial script

**Decision:** KEEP INTERACTIVE - Low impact, not recurring. Address manually.

### Tracking Candidates for Automation

Maintain a list of potential automation candidates in `.claude/automation-candidates.md`:

```markdown
# Automation Candidates

Track issues that might become automated checks if they recur.

## Under Observation

### Outdated Version References
- **First seen:** v0.6.5
- **Criteria met:** 1/5 (clear pass/fail only)
- **Action if recurs:** Automate with exclusions for CHANGELOG
- **Script:** `grep -r "v0\.6\." docs/ | grep -v CHANGELOG | grep -v "$(cat VERSION)"`

### Print Statements in Source
- **First seen:** v0.6.4, v0.6.5
- **Criteria met:** 2/5 (clear pass/fail, recurring)
- **Action if recurs again:** Automate as warning (non-blocking)
- **Script:** `grep -r "print(" src/ | grep -v "# print OK"`
```

**Review this file before each release to identify patterns.**

---

## Approval Workflow for Automated Checks

### When Automated Checks Fail

If an automated check fails, there are two paths:

#### Path 1: Fix the Issue (Recommended)

```bash
# Review what failed
less .hygiene-check-results-v0.6.6-rc1.txt

# Fix the issues
git add .
git commit -m "fix: address hygiene check failures"

# Retry (runs checks again)
git tag v0.6.6-rc2
```

#### Path 2: Review and Approve

For cases where failures are acceptable (documented exceptions, known complexity, etc.):

```bash
# Review failures thoroughly
less .hygiene-check-results-v0.6.6-rc1.txt

# If issues are genuinely acceptable, approve
./scripts/approve_hygiene_checks.sh v0.6.6-rc1

# Retry (now proceeds with approval)
git tag v0.6.6-rc1
```

**When to approve:**
- Known complexity in documented exceptions (get_tasks, update_task)
- Intentional TODOs with tracking issues
- Test coverage gaps with documented justification
- False positives from automated checks

**When NOT to approve:**
- Version mismatches (always fix)
- Test failures (always fix)
- Complexity violations in new code (refactor or document)
- Coverage below 85% without justification (add tests)

---

## Documentation Requirements

### For All Releases

- Update CHANGELOG.md with changes
- Update version references in documentation
- Verify all examples match current API

### For Minor Releases

**Additional requirements:**
- Run all 4 interactive quality checks
- Address critical issues found
- Document any newly discovered patterns in `.claude/automation-candidates.md`
- If API changes: Update API_REFERENCE.md
- If breaking changes: Create MIGRATION_vX.Y.md

### For Major Releases

**Additional requirements:**
- Complete migration guide
- External review of breaking changes
- Update architectural decision docs
- Communication plan for users

---

## Release Checklist

### Patch Release Checklist

**Before tagging RC:**
- [ ] All milestone issues closed
- [ ] CHANGELOG.md updated
- [ ] Version bumped in VERSION file

**RC tag (`v0.6.x-rc1`):**
- [ ] Pre-tag hook runs 7 automated checks
- [ ] All critical checks pass (or approved)
- [ ] Warnings reviewed and acceptable

**Final release:**
- [ ] Merge release branch to main
- [ ] Tag final release (`v0.6.x`)
- [ ] Push tags and create GitHub release
- [ ] Merge main back to development branches

### Minor Release Checklist

**Before tagging RC:**
- [ ] All milestone issues closed
- [ ] CHANGELOG.md updated
- [ ] Version bumped in VERSION file
- [ ] **Run `/doc-quality` and address critical issues**
- [ ] **Run `/code-quality` and address critical issues**
- [ ] **Run `/test-coverage` and address critical issues**
- [ ] **Run `/directory-check` and address critical issues**
- [ ] **Review `.claude/automation-candidates.md` for patterns**

**RC tag (`v0.x.0-rc1`):**
- [ ] Pre-tag hook prompts for quality check confirmation
- [ ] Confirm all 4 interactive checks run
- [ ] Pre-tag hook runs 7 automated checks
- [ ] All critical checks pass (or approved)
- [ ] Warnings reviewed and acceptable

**Final release:**
- [ ] Merge release branch to main
- [ ] Tag final release (`v0.x.0`)
- [ ] Push tags and create GitHub release
- [ ] Update `.claude/automation-candidates.md` with any new patterns
- [ ] Merge main back to development branches

### Major Release Checklist

Same as minor release, plus:
- [ ] Migration guide complete
- [ ] Breaking changes documented
- [ ] External review completed
- [ ] User communication sent
- [ ] Backwards compatibility assessed

---

## Summary

**Patch releases (v0.6.x):** Automated checks only (7 critical checks)

**Minor releases (v0.x.0):** Automated checks + 4 interactive quality reviews

**Major releases (vX.0.0):** Automated + interactive + manual review

**Automation criteria:** Clear pass/fail + consistent failures + high impact + low false positives + maintainable

**Enforcement:** Pre-tag hook prompts for confirmation that interactive checks were run for minor/major releases

**Tracking:** Maintain `.claude/automation-candidates.md` to identify patterns for future automation
