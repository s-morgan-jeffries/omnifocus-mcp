# Archived Scripts

These scripts are preserved for historical reference but are not actively maintained.

## Test Database Setup Experiments

### setup_clean_test_database.sh (v1)
**Date:** October 9, 2025
**Approach:** Programmatic database creation

**What it tried to do:**
- Quit OmniFocus automatically
- Create database structure programmatically
- Set up minimal test environment

**Why archived:**
- Replaced by `scripts/setup_test_database.sh` (primary production script)
- Experimental approach - not fully reliable
- Programmatic database creation proved difficult with OmniFocus

**Historical value:**
- Documents first attempt at automated test database setup
- Shows challenges with OmniFocus automation
- Reference for future automation attempts

---

### setup_clean_test_database_v2.sh (v2)
**Date:** October 9, 2025
**Approach:** Manual database creation with guided workflow

**What it tried to do:**
- Prompt user to create database via OmniFocus UI (File → New Database)
- Provide step-by-step instructions
- Set up test mode configuration

**Why archived:**
- Replaced by `scripts/setup_test_database.sh` (primary production script)
- Manual approach less convenient than primary script
- v2 iteration of experimental approach

**Historical value:**
- Documents manual workflow approach
- Shows evolution from v1 (programmatic) to v2 (guided manual)
- Reference for understanding final `setup_test_database.sh` design

---

## Mistake Tracking System (Legacy)

### mistake-tracking-legacy/ directory
**Date:** October 21, 2025 (Migrated to GitHub Issues)
**Status:** Complete migration, scripts archived for reference

**What it was:**
- Automated system for tracking and categorizing development mistakes
- Scripts for logging, analyzing, and preventing recurring mistakes
- Stored in `.claude/mistakes/` directory

**Scripts archived:**
- `log_mistake.sh` - Interactive mistake logging
- `update_mistake_status.sh` - Mark mistakes as resolved
- `verify_prevention.sh` - Check prevention measures exist
- `update_metrics.sh` - Generate mistake metrics
- `check_recurrence.sh` - Identify recurring patterns
- `test_prevention_measures.sh` - Verify prevention scripts work
- `check_monitoring_deadlines.sh` - Check mistake resolution deadlines
- `migrate_mistakes_to_issues.sh` - One-time migration script to GitHub Issues

**Why migrated:**
- GitHub Issues provides better tracking and visibility
- Integrated with pull requests and milestones
- Less maintenance overhead (no custom scripts needed)
- All 13 ai-process mistakes migrated to issues #31-43

**Using the new system:**
- Report mistakes as GitHub Issues with `ai-process` label
- Reference issue numbers in commits
- Track prevention measures in issue descriptions
- See `.claude/mistakes/README.md` for historical context

**Historical value:**
- Documents custom mistake tracking approach (v0.5.0 - v0.6.1)
- Shows evolution from local files to GitHub Issues
- Reference for systematic mistake prevention methodology

---

## Using These Scripts

**DO NOT use these scripts for new development.**

**Instead, use:**
- `scripts/setup_test_database.sh` - Primary test database setup script (production)

See `docs/guides/INTEGRATION_TESTING.md` for complete setup guide.

---

## Migration Notes

If you were previously using v1 or v2:
1. Delete your old `OmniFocus-TEST.ofocus` database
2. Run `scripts/setup_test_database.sh` to create a fresh test database
3. Follow the setup instructions in the output

The primary script combines the best elements of both v1 and v2 approaches with improved reliability.
