# Directory Audit - Action Items

**Audit Date:** 2025-10-25  
**Report:** `.claude/DIRECTORY_AUDIT_REPORT.md`

---

## QUICK REFERENCE: Issues Found

### Critical (High Priority)

1. **Mistake tracking migration incomplete** (8 scripts, 3 docs)
   - Location: `scripts/` + `.claude/mistakes/`
   - Issue: System migrated to GitHub Issues (Oct 21) but cleanup not done
   - Impact: Confusing for maintainers, orphaned scripts not being maintained
   - Effort: 20 min immediate, 1 hour total

2. **Redundant hook documentation** (3 documents)
   - Location: `docs/reference/`
   - Issue: CLAUDE_CODE_HOOKS.md, HOOKS_COMPARISON.md, and HOOK_SOLUTIONS_FOR_ALL_ISSUES.md have overlapping content
   - Impact: Reader confusion, maintenance overhead
   - Effort: 1-2 hours

### Medium Priority

3. **Dual hook systems** (git hooks vs Claude Code hooks)
   - Location: `scripts/git-hooks/` and `scripts/hooks/`
   - Issue: Both exist, but Claude Code hooks (v0.6.2+) are the new standard
   - Impact: Documentation confusion, outdated git hooks may be installed
   - Effort: 30 min to clarify, 1 hour to consolidate

4. **Historical document in active directory**
   - Location: `docs/project/GITHUB_ISSUES_MIGRATION_PLAN.md`
   - Issue: Describes completed migration, belongs in archive
   - Impact: New contributors confused about project management structure
   - Effort: 15 min

---

## Implementation Checklist

### Sprint 1 (Immediate - 1 hour)

- [ ] **Create archive directory for mistake tracking scripts**
  ```bash
  mkdir -p scripts/archive/mistake-tracking-legacy
  # Move these files:
  # - log_mistake.sh
  # - update_mistake_status.sh
  # - verify_prevention.sh
  # - update_metrics.sh
  # - check_recurrence.sh
  # - test_prevention_measures.sh
  # - check_monitoring_deadlines.sh
  # - migrate_mistakes_to_issues.sh
  ```
  - Update `scripts/archive/README.md` with new section explaining mistake tracking migration
  - Update `scripts/README.md` to remove references to these scripts

- [ ] **Document hook situation in CLAUDE.md**
  - Add note: "Git hooks (v0.6.1 and earlier) deprecated in v0.6.2+ in favor of Claude Code hooks"
  - Point to `docs/reference/CLAUDE_CODE_HOOKS.md`
  - Explain both systems exist but Claude Code hooks are primary
  - Update `scripts/README.md` Quick Reference table to note git hooks as legacy

### Sprint 2 (Next Release - 1-2 hours)

- [ ] **Create hooks documentation guide**
  - Create `docs/reference/HOOKS_README.md` OR
  - Update `docs/reference/README.md` with hook documentation guide
  - Explain:
    - CLAUDE_CODE_HOOKS.md = philosophy, event types, blocking mechanisms (deep dive)
    - HOOKS_COMPARISON.md = when to use each hook system (quick reference)
    - HOOK_SOLUTIONS_FOR_ALL_ISSUES.md = implementation examples (recipes)
  - Reader flow: Start with README, then pick one based on question

- [ ] **Move historical document to archive**
  - Move `docs/project/GITHUB_ISSUES_MIGRATION_PLAN.md` → `docs/archive/`
  - Create `docs/project/README.md` explaining:
    - This directory contains: ROADMAP.md (current work), future plans
    - NOT historical documents (those go in archive/)
  - Update cross-references

- [ ] **Create README files for active directories**
  - Create `docs/research/README.md` explaining:
    - Purpose: Location for ongoing feature/architecture research
    - Convention: Use date-based filenames (YYYY-MM-DD-*)
    - Examples: automation research, API considerations, etc.

### Maintenance (Ongoing)

- [ ] **Review `.claude/mistakes/` status quarterly**
  - Check if `METRICS.md` should be regenerated (currently broken per ANALYSIS_GAPS.md)
  - OR: Mark entire directory as "Archived Oct 2025, kept for historical reference"
  - Update CLAUDE.md to reference GitHub Issues for all new issue tracking

- [ ] **Remove deprecated git hooks (v1.0)**
  - Decide: Keep git hooks for backward compat or remove entirely?
  - If removing: Archive to `scripts/archive/git-hooks-legacy/` with explanation
  - If keeping: Clarify in documentation that they're superseded by Claude Code hooks

- [ ] **Document `scripts/setup_github_labels.sh` status**
  - Is this a one-time setup script or active maintenance tool?
  - If one-time: Move to archive with explanation
  - If active: Update documentation about when/how to use

---

## Files to Move/Archive

### Immediate Moves

```
scripts/archive/mistake-tracking-legacy/
├── log_mistake.sh
├── update_mistake_status.sh
├── verify_prevention.sh
├── update_metrics.sh
├── check_recurrence.sh
├── test_prevention_measures.sh
├── check_monitoring_deadlines.sh
└── migrate_mistakes_to_issues.sh

# Also: Update .claude/mistakes/ARCHIVE_NOTICE.md to reference GitHub Issues
```

### Secondary Moves (Sprint 2)

```
docs/archive/
├── GITHUB_ISSUES_MIGRATION_PLAN.md  # Move from docs/project/
└── [existing archive structure]
```

---

## Files That Are OK (No Action)

These are well-organized and don't need changes:

- `.claude/CLAUDE.md` - Active, up-to-date ✅
- `.claude/CLAUDE-redesign-phase.md` - Archived with clear notice ✅
- `.claude/mistakes/ARCHIVE_NOTICE.md` - Clear explanation ✅
- `scripts/archive/` - Well-documented ✅
- `docs/archive/` - Excellent archive structure ✅
- `docs/guides/` - Clear, current ✅
- `docs/reference/` (core files) - Well-maintained ✅

---

## Best Practices to Continue

1. ✅ Archive notices in every archive directory
2. ✅ README.md in every directory explaining purpose
3. ✅ Date-based naming for research files (YYYY-MM-DD-*)
4. ✅ Version-based migration guides (v0.X.md pattern)
5. ✅ Clear separation of active vs historical

---

## Questions for Review

**Before implementing, clarify:**

1. Should `.claude/mistakes/` be deleted, archived, or kept as historical reference?
   - Current status: ARCHIVE_NOTICE.md exists but METRICS.md is broken
   - Recommendation: Keep entire directory as "Historical Archive" with clear notice

2. Should git hooks be completely removed or kept as fallback?
   - Current status: Both git hooks and Claude Code hooks exist
   - Recommendation: Archive git hooks with migration guide; Claude Code hooks are primary

3. Is `scripts/setup_github_labels.sh` one-time or recurring?
   - Current status: No documentation about its purpose
   - Recommendation: Document status in scripts/README.md or archive

---

## Effort Estimates

| Task | Effort | Priority |
|------|--------|----------|
| Move mistake tracking scripts to archive | 20 min | IMMEDIATE |
| Update documentation for hook situation | 30 min | IMMEDIATE |
| Consolidate hook documentation | 1-2 hours | NEXT SPRINT |
| Move historical docs to archive | 30 min | NEXT SPRINT |
| Create README files | 30 min | NEXT SPRINT |
| **Total Immediate** | **50 min** | |
| **Total Next Sprint** | **2-2.5 hours** | |

---

## Cross-References

- Full audit report: `.claude/DIRECTORY_AUDIT_REPORT.md`
- Issue tracking system: GitHub Issues (migrated from `.claude/mistakes/MISTAKES.md`)
- Hook documentation: `docs/reference/CLAUDE_CODE_HOOKS.md` (primary reference)
- Development workflow: `docs/guides/CONTRIBUTING.md`
