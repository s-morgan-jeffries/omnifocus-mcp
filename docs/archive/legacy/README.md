# Legacy Documentation Archive

This directory contains **early project documentation** (pre-v0.5.0, September-October 2025).

## Purpose

These documents were created during the **initial implementation phases** before the major architectural decisions that shaped v0.6.0.

**Historical value:**
- Understanding early design thinking
- Seeing how requirements evolved
- Learning from initial approaches

**Why "legacy":**
- Created before v0.6.0 API redesign (40+ functions → 16)
- Some recommendations superseded by architectural principles
- Useful for context but not current guidance

## Documents

### APPLESCRIPT_AUDIT_FINDINGS.md
AppleScript property audit from v0.5.0 development. Found all needed timestamps and properties for task/project management.

**Superseded by:** `../../reference/APPLESCRIPT_GOTCHAS.md` (current AppleScript guidance)

### IMPLEMENTATION_EXAMPLES.md
Early implementation patterns and examples from initial development.

**Superseded by:** `../../ARCHITECTURE.md` (worked examples and patterns)

### SCHEMA_REVIEW.md
Detailed OmniFocus schema analysis (59KB document). Deep dive into OmniFocus database structure, properties, and relationships.

**Still relevant for:** Understanding OmniFocus internals when implementing new features

**Note:** Very detailed - use for deep dives only when working with new OmniFocus properties

### USE_CASES.md
15 use case analyses including out-of-scope features (email integration, calendar sync, etc.).

**Still relevant for:** Understanding project scope decisions and why certain features are excluded

**Superseded by:** `../../project/ROADMAP.md` for in-scope features

## Current Documentation

For current guidance, see:
- **Architecture Principles:** `../../ARCHITECTURE.md`
- **API Reference:** `../../reference/API_REFERENCE.md`
- **Contributing Guide:** `../../guides/CONTRIBUTING.md`
- **Testing Strategy:** `../../guides/TESTING.md`

## Why Keep These?

These documents provide valuable historical context:
1. Show the evolution of project thinking
2. Document decisions about what NOT to implement
3. Preserve detailed OmniFocus schema research
4. Help understand why current architecture exists

If you're working on a new feature and wondering "did we consider this?", these documents may have the answer.

## Last Updated

- Archive section created: October 11, 2025
- README added: October 20, 2025
