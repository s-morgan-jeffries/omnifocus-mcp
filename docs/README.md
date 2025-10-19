# OmniFocus MCP Server Documentation

Welcome to the OmniFocus MCP Server documentation! This directory contains comprehensive guides for contributing to and understanding the project.

**Last Updated:** 2025-10-19
**Project Version:** v0.6.0 (Maintenance Mode)

---

## Quick Start

**New contributors start here:**

1. **[Contributing Guide](CONTRIBUTING.md)** - Development workflow, TDD requirements, and pre-commit checklist
2. **[Testing Guide](TESTING.md)** - How to run tests and understand coverage
3. **[Architecture Principles](ARCHITECTURE.md)** - Design decisions and API patterns

**For daily development:**
- See `.claude/CLAUDE.md` for quick reference and critical rules
- Run `make test` before every commit
- Follow the architecture decision tree before adding functions

---

## Architecture & Design

### Core Documentation

- **[Architecture Principles](ARCHITECTURE.md)** - Complete design rationale with worked examples
  - Why we consolidated 40+ functions → 16 core functions
  - CRUD patterns and anti-patterns
  - Decision tree for when to add new functions
  - Type safety guidelines

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
  - All 16 core functions with signatures
  - Parameter descriptions and return formats
  - Migration guide from deprecated functions
  - Usage examples

### Implementation Guides

- **[AppleScript Gotchas](APPLESCRIPT_GOTCHAS.md)** - Known limitations and workarounds
  - Rich text note limitations
  - Variable naming conflicts
  - Recurring task patterns
  - Performance characteristics
  - Common error patterns

- **[Code Quality Standards](CODE_QUALITY.md)** - Complexity metrics and guidelines
  - Cyclomatic complexity targets (A-B-C-D-F ratings)
  - Radon configuration and thresholds
  - Intentionally complex functions (documented)
  - When to document vs refactor

---

## Testing

- **[Testing Guide](TESTING.md)** - Complete testing strategy
  - Three-level testing approach (unit, integration, E2E)
  - Test coverage statistics (89% overall)
  - Test organization and structure
  - How to run specific test suites

- **[Integration Testing](INTEGRATION_TESTING.md)** - Real OmniFocus testing
  - Test database setup
  - Environment configuration
  - Troubleshooting common issues
  - When integration tests are required

---

## Project Management

- **[Roadmap](ROADMAP.md)** - Project phases and current status
  - Phase 1: Foundation (COMPLETE)
  - Phase 2: Additional Primitives (COMPLETE)
  - Phase 3: API Redesign (COMPLETE - v0.6.0)
  - Technology stack
  - Future considerations

- **[Changelog](../CHANGELOG.md)** - Version history and technical changes
  - v0.6.0: API Redesign (40→16 functions, BREAKING)
  - v0.5.0: Claude Desktop compatibility
  - Migration guides for breaking changes
  - Bug fixes and improvements

- **[API Redesign Plan](archive/planning/API_REDESIGN_PLAN.md)** - Historical implementation roadmap (archived)
  - Original 40-function analysis
  - Consolidation strategy
  - Implementation phases
  - Completed v0.6.0 checklist

---

## Contributing

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
  - Before every commit checklist
  - Test-Driven Development (TDD) requirements
  - Code quality standards
  - When to update documentation
  - Pull request process

- **[Project Memory](../.claude/CLAUDE.md)** - Daily development reference
  - Critical rules (TDD, code quality)
  - Architecture quick reference
  - Decision tree for adding functions
  - Pre-commit checklist
  - Documentation index

---

## Archive

**Historical documentation (reference only):**

- **[Redesign-Phase Project Memory](../.claude/CLAUDE-redesign-phase.md)** - Implementation guidance archive
  - Preserved from active redesign phase
  - Detailed step-by-step implementation instructions
  - Migration patterns and strategies
  - Useful for future major refactors

---

## Documentation Map

```
docs/
├── README.md                    # This file - documentation index
├── ARCHITECTURE.md              # Design decisions and patterns
├── API_REFERENCE.md             # Complete API documentation
├── APPLESCRIPT_GOTCHAS.md       # Known limitations and workarounds
├── CODE_QUALITY.md              # Complexity guidelines
├── CONTRIBUTING.md              # Development workflow
├── INTEGRATION_TESTING.md       # Real OmniFocus testing setup
├── MIGRATION_v0.5.md            # v0.4 → v0.5 migration guide
├── MIGRATION_v0.6.md            # v0.5 → v0.6 migration guide
├── ROADMAP.md                   # Project phases and status
├── TESTING.md                   # Testing strategy and coverage
├── archive/                     # Historical documentation
│   └── planning/
│       └── API_REDESIGN_PLAN.md # v0.6.0 implementation plan (complete)
└── research/                    # Technical research documents
```

---

## Quick Links

**I want to...**

- **Add a new function** → Check [Architecture: Decision Tree](ARCHITECTURE.md#quick-decision-tree) first
- **Understand why the API is designed this way** → Read [Architecture](ARCHITECTURE.md)
- **Run tests** → See [Testing Guide](TESTING.md) or run `make test`
- **Fix a bug** → Follow [Contributing: Before Every Commit](CONTRIBUTING.md#before-every-commit)
- **Understand AppleScript errors** → Check [AppleScript Gotchas](APPLESCRIPT_GOTCHAS.md)
- **See what changed in v0.6.0** → Read [Changelog v0.6.0](../CHANGELOG.md#060---2025-10-18)
- **Understand project history** → Review [Roadmap](ROADMAP.md)
- **Check code complexity** → Run `./scripts/check_complexity.sh` or see [Code Quality](CODE_QUALITY.md)

---

## External Resources

- **OmniFocus:** https://www.omnigroup.com/omnifocus
- **Model Context Protocol (MCP):** https://modelcontextprotocol.io/
- **FastMCP Framework:** https://github.com/jlowin/fastmcp
- **Claude Code:** https://docs.claude.com/en/docs/claude-code/

---

**Questions?**

1. Check this README for the right doc
2. Review `.claude/CLAUDE.md` for quick reference
3. Search relevant specialized doc
4. Ask in GitHub issues if still unclear

**Happy coding!** 🚀
