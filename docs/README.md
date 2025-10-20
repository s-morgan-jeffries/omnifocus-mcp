# OmniFocus MCP Server Documentation

Welcome to the OmniFocus MCP Server documentation! This directory contains comprehensive guides for contributing to and understanding the project.

**Last Updated:** 2025-10-20
**Project Version:** v0.6.1 (Maintenance Mode)

---

## Quick Start

**New contributors start here:**

1. **[Contributing Guide](guides/CONTRIBUTING.md)** - Development workflow, TDD requirements, and pre-commit checklist
2. **[Testing Guide](guides/TESTING.md)** - How to run tests and understand coverage
3. **[Architecture Principles](reference/ARCHITECTURE.md)** - Design decisions and API patterns

**For daily development:**
- See `../.claude/CLAUDE.md` for quick reference and critical rules
- Run `make test` before every commit
- Follow the architecture decision tree before adding functions

---

## Documentation by Purpose

### 📚 Developer Guides (Read First)

Daily development workflow and practices:

- **[Contributing Guide](guides/CONTRIBUTING.md)** - Development workflow and checklist
- **[Testing Guide](guides/TESTING.md)** - Testing strategy, coverage, and procedures  
- **[Integration Testing](guides/INTEGRATION_TESTING.md)** - Real OmniFocus testing setup

### 🔍 Reference Documentation (Consult as Needed)

Architecture and implementation reference:

- **[Architecture Principles](reference/ARCHITECTURE.md)** - Design rationale with worked examples
  - Why we consolidated 40+ functions → 16 core functions
  - CRUD patterns and anti-patterns
  - Decision tree for when to add new functions
  - Type safety guidelines

- **[API Reference](reference/API_REFERENCE.md)** - Complete API documentation
  - All 16 core functions with signatures
  - Parameter descriptions and return formats
  - Migration guide from deprecated functions
  - Usage examples

- **[Code Quality Standards](reference/CODE_QUALITY.md)** - Complexity metrics and guidelines
  - Cyclomatic complexity targets (A-B-C-D-F ratings)
  - Radon configuration and thresholds
  - Intentionally complex functions (documented)
  - When to document vs refactor

- **[AppleScript Gotchas](reference/APPLESCRIPT_GOTCHAS.md)** - Known limitations and workarounds
  - Rich text note limitations
  - Variable naming conflicts
  - Recurring task patterns
  - Performance characteristics
  - Common error patterns

### 🔄 Migration Guides (Version-Specific)

Upgrade guides for version transitions:

- **[Migration Index](migration/README.md)** - All migration guides with upgrade paths
- **[v0.5 Migration](migration/v0.5.md)** - v0.4 → v0.5 upgrade guide
- **[v0.6 Migration](migration/v0.6.md)** - v0.5 → v0.6 upgrade guide (major redesign: 40→16 functions)

### 📋 Project Management

Project status and roadmap:

- **[Project Roadmap](project/ROADMAP.md)** - Project phases, history, and current status
- **[Changelog](../CHANGELOG.md)** - Version history and technical changes

### 🗄️ Archive

Historical documentation (reference only):

- **[Archive Index](archive/README.md)** - Historical planning, research, and legacy docs
  - Planning documents from v0.6.0 redesign phase
  - Research from pre-v0.6.0 (attachments, recurring tasks, etc.)
  - Legacy documentation from early project phases

---

## Quick Links

**I want to...**

- **Add a new function** → Check [Architecture: Decision Tree](reference/ARCHITECTURE.md#quick-decision-tree) first
- **Understand why the API is designed this way** → Read [Architecture](reference/ARCHITECTURE.md)
- **Run tests** → See [Testing Guide](guides/TESTING.md) or run `make test`
- **Fix a bug** → Follow [Contributing: Before Every Commit](guides/CONTRIBUTING.md#before-every-commit)
- **Understand AppleScript errors** → Check [AppleScript Gotchas](reference/APPLESCRIPT_GOTCHAS.md)
- **Upgrade from v0.5** → Read [v0.6 Migration Guide](migration/v0.6.md)
- **See what changed recently** → Review [Changelog](../CHANGELOG.md)
- **Understand project history** → Review [Roadmap](project/ROADMAP.md)
- **Check code complexity** → Run `./scripts/check_complexity.sh` or see [Code Quality](reference/CODE_QUALITY.md)

---

## Directory Structure

```
docs/
├── README.md                       # This file - documentation index
│
├── guides/                         # Daily developer guides
│   ├── CONTRIBUTING.md
│   ├── TESTING.md
│   └── INTEGRATION_TESTING.md
│
├── reference/                      # Architecture & API reference
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── CODE_QUALITY.md
│   └── APPLESCRIPT_GOTCHAS.md
│
├── migration/                      # Version migration guides
│   ├── README.md
│   ├── v0.5.md
│   └── v0.6.md
│
├── project/                        # Project management
│   └── ROADMAP.md
│
└── archive/                        # Historical documentation
    ├── README.md
    ├── planning/                   # Planning phase docs
    ├── research/                   # Technical research (pre-v0.6.0)
    └── legacy/                     # Early project docs
```

---

## External Resources

- **OmniFocus:** https://www.omnigroup.com/omnifocus
- **Model Context Protocol (MCP):** https://modelcontextprotocol.io/
- **FastMCP Framework:** https://github.com/jlowin/fastmcp
- **Claude Code:** https://docs.claude.com/en/docs/claude-code/

---

**Questions?**

1. Check this README for the right doc
2. Review `../.claude/CLAUDE.md` for quick reference
3. Search relevant specialized doc
4. Ask in GitHub issues if still unclear

**Happy coding!**
