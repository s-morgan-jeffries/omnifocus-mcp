# Documentation Archive

This directory contains historical documentation from the OmniFocus MCP Server development process.

## Purpose

These documents were created during the planning and research phases (October 2025) but are now **obsolete** as the project has completed Phases 1 and 2 and moved into refinement (v0.5.0).

**They are preserved for historical reference only.**

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

For current, active documentation, see:

### Core Documentation (Main `docs/` Directory)
- **README.md** - Main project README with quick start and tool reference
- **CHANGELOG.md** - Version history and release notes
- **ROADMAP.md** - Current status and future plans
- **TESTING.md** - Testing guide (updated with v0.5.0 test counts)
- **MIGRATION_v0.5.md** - Migration guide for v0.4 → v0.5
- **APPLESCRIPT_AUDIT_FINDINGS.md** - AppleScript interface audit results
- **USE_CASES.md** - Comprehensive use case documentation (trimmed to in-scope features)

### Research Documentation (`docs/research/`)
Active research documents for technical decisions:
- **applescript-vs-omni-automation.md** - Comparison of automation approaches
- **attachment-api-research.md** - File attachment capabilities research
- **recurring-tasks-research.md** - Recurring task implementation research
- **jxa-attachment-module-design.md** - JavaScript for Automation design
- **mcp-unified-interface.md** - MCP interface design decisions
- **tool-consolidation-analysis.md** - Tool consolidation decisions (v0.5.0)
- **tool-documentation-audit.md** - Documentation audit results

### Reference
- **SCHEMA_REVIEW.md** - Canonical OmniFocus schema reference (main docs/)
- **omnifocus-4.8.4-documentation.html** - Official OmniFocus 4.8.4 documentation

## Why Archive Instead of Delete?

These documents provide valuable historical context:

1. **Decision history** - Why certain features are out of scope
2. **Research process** - How we evaluated different approaches
3. **Planning evolution** - How the project scope evolved over time
4. **Lessons learned** - What worked and what didn't

## Last Updated

Archive created: October 11, 2025
Project version when archived: v0.5.0
