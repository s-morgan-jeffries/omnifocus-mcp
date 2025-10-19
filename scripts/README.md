# Scripts

Utility scripts for development, testing, and maintenance of the OmniFocus MCP server.

## Quick Reference

### Mistake Tracking & Prevention

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `log_mistake.sh` | Log architectural mistakes for tracking | When catching high-level mistakes |
| `update_mistake_status.sh` | Update mistake lifecycle status | During mistake resolution |
| `update_metrics.sh` | Update METRICS.md statistics | After mistake changes |
| `verify_prevention.sh` | Validate prevention implementation | Before marking mistake resolved |
| `check_version_sync.sh` | Validate version across all files | Before version bumps / releases |
| `check_test_count_sync.sh` | Validate TESTING.md matches pytest | Before commits with test changes |
| `install-git-hooks.sh` | Install pre-commit/commit-msg hooks | First-time setup / hook updates |

### Code Quality & Parity

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `analyze_tool_docs.py` | Analyze MCP tool documentation quality | After adding/updating tools |
| `check_client_server_parity.sh` | Verify all client functions exposed in server | Before commits (in checklist) |
| `check_complexity.sh` | Check code cyclomatic complexity | Before commits (in checklist) |

### Integration Testing

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup_test_database.sh` | Create OmniFocus test database | First-time integration test setup |
| `setup_clean_test_database.sh` | Create minimal test database | Integration test setup (v1) |
| `setup_clean_test_database_v2.sh` | Create minimal test database | Integration test setup (v2) |
| `setup_comprehensive_test_data.sh` | Populate test database with data | Integration test data setup |
| `cleanup_test_data.sh` | Remove test data from database | After integration tests |
| `cleanup_comprehensive_test_data.sh` | Remove comprehensive test data | After comprehensive tests |
| `run_integration_tests.sh` | Run integration tests with setup | Full integration test workflow |

---

## analyze_tool_docs.py

**Purpose**: Analyze MCP tool documentation quality for Claude Desktop

**Usage**:
```bash
python3 scripts/analyze_tool_docs.py
```

**When to use**:
- After adding new MCP tools
- When updating tool descriptions
- To verify documentation consistency
- To identify potentially ambiguous tools

**Output**:
- Tool count and categorization
- Returns section coverage
- Short description warnings
- Potential confusion points
- Recommendations for improvements

**Example**:
```
📊 Total tools: 16
✓ Tools with Returns section: 16 (100%)
⚠️  POTENTIAL CLAUDE DESKTOP CONFUSION POINTS
...
```

---

## check_client_server_parity.sh

**Purpose**: Verify all client functions have corresponding MCP tools in server

**Usage**:
```bash
./scripts/check_client_server_parity.sh
```

**When to use**:
- Before every commit (part of pre-commit checklist)
- After implementing new client functions
- To catch missing server exposure

**What it checks**:
- Extracts all public functions from `omnifocus_client.py`
- Extracts all `@mcp.tool()` decorated functions from `server_fastmcp.py`
- Reports any client functions missing MCP tool wrappers

**Exit codes**:
- `0`: All client functions exposed ✅
- `1`: Missing server exposure ❌

---

## check_complexity.sh

**Purpose**: Check code cyclomatic complexity using Radon

**Usage**:
```bash
./scripts/check_complexity.sh
```

**When to use**:
- Before every commit (part of pre-commit checklist)
- After implementing complex functions
- To identify code that needs refactoring or documentation

**Complexity ratings**:
- **A-B (CC 1-10)**: Simple, easy to test ✅
- **C (CC 11-20)**: Acceptable for complex logic ⚠️
- **D-F (CC 21+)**: Requires documentation or refactoring 🔴

See `docs/reference/CODE_QUALITY.md` for complete guidelines.

---

## log_mistake.sh

**Purpose**: Log high-level architectural and workflow mistakes for tracking

**Usage**:
```bash
./scripts/log_mistake.sh
# Then edit .claude/MISTAKES.md to fill in details
```

**When to use**:
- When you catch an architectural oversight (not syntax errors)
- Examples: missing e2e tests, missing server exposure, violated TDD, missing docs

**What it does**:
- Auto-increments mistake number (MISTAKE-001, MISTAKE-002, etc.)
- Inserts template into `.claude/MISTAKES.md`
- Updates mistake count statistics

**Workflow**:
1. Fix the mistake first
2. Run `./scripts/log_mistake.sh`
3. Edit `.claude/MISTAKES.md` to fill in details
4. Reference in commit: `Resolves: MISTAKE-XXX`

See `.claude/MISTAKES.md` and `.claude/METRICS.md` for the tracking system.

---

## update_mistake_status.sh

**Purpose**: Update the lifecycle status of a logged mistake

**Usage**:
```bash
./scripts/update_mistake_status.sh MISTAKE-XXX <status> [details]
```

**Status options**:
- `open` - Newly logged, not being worked on
- `fixing` - Currently implementing the fix
- `prevention-pending` - Fix implemented, prevention not yet added
- `monitoring` - Prevention implemented, monitoring effectiveness
- `resolved` - Prevention validated, no recurrence
- `archived` - Old mistake, moved to historical record

**When to use**:
- After fixing a mistake: Update to `prevention-pending`
- After adding prevention: Update to `monitoring`
- After validating prevention works: Update to `resolved`

**Example**:
```bash
./scripts/update_mistake_status.sh MISTAKE-001 resolved
```

---

## update_metrics.sh

**Purpose**: Automatically update METRICS.md with statistics from MISTAKES.md

**Usage**:
```bash
./scripts/update_metrics.sh
```

**When to use**:
- After logging new mistakes
- After changing mistake statuses
- Before reviewing project metrics

**What it updates**:
- Total mistake count
- Category breakdown
- Status breakdown
- Recurrence counts

---

## verify_prevention.sh

**Purpose**: Validate that prevention measures were actually implemented

**Usage**:
```bash
./scripts/verify_prevention.sh MISTAKE-XXX
```

**When to use**:
- Before marking a mistake as `resolved`
- During mistake reviews
- To audit prevention implementation

**What it checks**:
- If prevention mentions CLAUDE.md, verifies it was updated
- If prevention mentions CONTRIBUTING.md, verifies update after discovery
- If prevention mentions scripts, verifies they exist
- Validates Prevention Status checkbox is marked

**Example**:
```bash
./scripts/verify_prevention.sh MISTAKE-001
```

---

## check_version_sync.sh

**Purpose**: Validate version numbers are synchronized across all files (Addresses MISTAKE-003)

**Usage**:
```bash
./scripts/check_version_sync.sh
```

**When to use**:
- Before version bumps
- Before releases
- During pre-commit checks

**What it checks**:
- `pyproject.toml` (authoritative source)
- `.claude/CLAUDE.md` "Current Version" line
- `CHANGELOG.md` version headers
- `README.md` version references

**Exit codes**:
- `0`: All versions synchronized ✅
- `1`: Version mismatch detected ❌

---

## check_test_count_sync.sh

**Purpose**: Validate TESTING.md test count matches actual pytest output (Addresses MISTAKE-002)

**Usage**:
```bash
./scripts/check_test_count_sync.sh
```

**When to use**:
- Before commits that add/remove tests
- During documentation updates
- As part of CI/CD validation

**What it checks**:
- Runs `make test` to get actual test count
- Compares with `docs/guides/TESTING.md` documented count
- Reports mismatches with actionable fix instructions

**Exit codes**:
- `0`: Test counts match ✅
- `1`: Test count mismatch detected ❌

---

## install-git-hooks.sh

**Purpose**: Install git hooks for automated mistake detection and enforcement

**Usage**:
```bash
./scripts/install-git-hooks.sh
```

**When to use**:
- First-time repository setup
- After updating git hook scripts
- When hooks are accidentally removed

**What it installs**:
1. **pre-commit hook** - Detects 6 types of mistakes before commit:
   - Missing tests (modified client without test changes)
   - Missing server exposure (new function not in server)
   - Missing migration guides (CHANGELOG references missing file)
   - Version sync issues (version bump without doc updates)
   - Test count sync issues (test changes without TESTING.md update)
   - Complexity spikes (new high-complexity code)

2. **commit-msg hook** - Enforces proper mistake resolution format:
   - Validates "Resolves: MISTAKE-XXX" format
   - Ensures referenced mistake exists in MISTAKES.md

**To uninstall**:
```bash
rm .git/hooks/pre-commit .git/hooks/commit-msg
```

---

## Integration Test Scripts

### setup_test_database.sh

**Purpose**: Create a test OmniFocus database for integration testing

**Usage**:
```bash
./scripts/setup_test_database.sh
```

**When to use**:
- First-time setup for integration tests
- Creating a fresh test database

**What it does**:
- Creates `OmniFocus-TEST.ofocus` database
- Prompts you to open it in OmniFocus
- Provides instructions for test mode configuration

See `docs/guides/INTEGRATION_TESTING.md` for complete setup guide.

---

### setup_comprehensive_test_data.sh

**Purpose**: Populate test database with comprehensive test data

**Usage**:
```bash
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
./scripts/setup_comprehensive_test_data.sh
```

**When to use**:
- After creating test database
- Before running integration tests
- To create realistic test scenarios

**What it creates**:
- Test projects with various statuses
- Test tasks with different properties
- Test folders and tags

---

### cleanup_test_data.sh / cleanup_comprehensive_test_data.sh

**Purpose**: Remove test data from test database

**Usage**:
```bash
export OMNIFOCUS_TEST_MODE=true
./scripts/cleanup_test_data.sh
# or
./scripts/cleanup_comprehensive_test_data.sh
```

**When to use**:
- After integration tests complete
- To reset test database to clean state

**Safety**: Requires `OMNIFOCUS_TEST_MODE=true` to prevent accidental production data deletion

---

### run_integration_tests.sh

**Purpose**: Run complete integration test workflow

**Usage**:
```bash
./scripts/run_integration_tests.sh
```

**When to use**:
- Running full integration test suite
- Automated testing workflow

**What it does**:
- Sets up test environment
- Runs integration tests
- Cleans up test data

---

## Development Workflow

**Before every commit:**
```bash
./scripts/check_client_server_parity.sh  # Verify server exposure
./scripts/check_complexity.sh             # Check code complexity
make test                                 # Run unit tests
```

**When implementing new features:**
```bash
# 1. Write tests first (TDD)
# 2. Implement client function
# 3. Expose in server_fastmcp.py
# 4. Verify parity
./scripts/check_client_server_parity.sh
# 5. Check complexity
./scripts/check_complexity.sh
```

**For integration testing:**
```bash
# One-time setup
./scripts/setup_test_database.sh

# Before tests
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
./scripts/setup_comprehensive_test_data.sh

# Run tests
make test-integration

# Cleanup
./scripts/cleanup_comprehensive_test_data.sh
```
