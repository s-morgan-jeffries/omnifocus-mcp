# Documentation Archive

This directory contains historical documentation from the OmniFocus MCP Server development process.

## Purpose

These documents were created during the planning and research phases (October 2025) but are now **obsolete** as the project has completed the major API redesign (v0.6.0, October 2025).

**They are preserved for historical reference only.**

**Note:** This archive was created during v0.5.0 (October 11, 2025). The project has since advanced to v0.6.0 (October 19, 2025) with a major API redesign (40+ functions → 16 core tools). Some references below may be outdated. See main `docs/` directory for current information.

## Directory Structure

### `planning/`
Documents created during the implementation planning phase:

- **90_PERCENT_COVERAGE_PLAN.md** - Test coverage planning (now achieved: 89%)
- **ANALYSIS_COMPLETE.md** - Research phase summary and executive overview
- **QUICK_START_GUIDE.md** - Week-by-week implementation guide for Phase 1-2
- **gap-analysis.md** - Early gap analysis from research phase
- **implementation-roadmap.md** - Alternative roadmap document (superseded by ROADMAP.md)

**Status:** Phase 1 & 2 complete ✅. Email integration and other Phase 3-4 features deemed out of scope for MCP server.

### `research/`
Analysis documents for features that were researched but determined to be out of scope:

- **USE_CASES_ANALYSIS.md** - Detailed analysis of 15 use cases including email/calendar integration
- **USE_CASES_SUMMARY.md** - Summary of use case analysis
- **SCHEMA_CHANGES_VISUAL.md** - Visual representation of schema evolution (historical)
- **SCHEMA_REVIEW_SUMMARY.md** - Summary of schema review (superseded by SCHEMA_REVIEW.md)

**Status:** Out-of-scope features (email, calendar, meeting transcription) should be implemented as separate services that *use* the MCP server, not as part of the server itself.

## Current Documentation

For current, active documentation, see the new organized structure:

### Developer Guides (`docs/guides/`)
- **CONTRIBUTING.md** - Development workflow, TDD requirements, pre-commit checklist
- **TESTING.md** - Testing strategy, coverage, and procedures
- **INTEGRATION_TESTING.md** - Real OmniFocus testing setup and troubleshooting

### Reference Documentation (`docs/reference/`)
- **ARCHITECTURE.md** - Design decisions, CRUD patterns, decision tree
- **API_REFERENCE.md** - Complete API documentation for all 16 core functions
- **CODE_QUALITY.md** - Complexity metrics, Radon guidelines, quality standards
- **APPLESCRIPT_GOTCHAS.md** - Known limitations, workarounds, common errors

### Migration Guides (`docs/migration/`)
- **v0.5.md** - v0.4 → v0.5 migration guide
- **v0.6.md** - v0.5 → v0.6 migration guide (major redesign)

### Project Management (`docs/project/`)
- **ROADMAP.md** - Project phases, history, and current status

## Why Archive Instead of Delete?

These documents provide valuable historical context:

1. **Decision history** - Why certain features are out of scope
2. **Research process** - How we evaluated different approaches
3. **Planning evolution** - How the project scope evolved over time
4. **Lessons learned** - What worked and what didn't

## Last Updated

Archive created: October 11, 2025
Project version when archive created: v0.5.0
Last reviewed: October 19, 2025 (Project now at v0.6.0)
