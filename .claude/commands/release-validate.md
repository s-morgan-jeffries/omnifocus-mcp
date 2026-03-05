Validate readiness for an OmniFocus MCP release. Run this before creating RC tags.

## Steps

1. **Check version sync** across all files:
   ```bash
   ./scripts/check_version_sync.sh
   ```

2. **Check client-server parity** (all connector functions exposed in server):
   ```bash
   ./scripts/check_client_server_parity.sh
   ```

3. **Run complexity check:**
   ```bash
   ./scripts/check_complexity.sh
   ```

4. **Run full test suite:**
   ```bash
   make test
   ```

5. **Run integration tests** (requires OmniFocus + test database):
   ```bash
   make test-integration
   ```

6. **Run E2E tests:**
   ```bash
   make test-e2e
   ```

7. **Check CHANGELOG.md:**
   - If on a release branch: verify CHANGELOG has all changes, date can be "TBD"
   - If about to finalize: verify date is set (not "TBD") BEFORE merging to main

8. **Check README.md:**
   - Version numbers match release
   - New features listed in appropriate tool categories
   - Installation examples are current

9. **Summarize results:**
   - List any failures or warnings
   - Recommend: ready to tag, or list blocking issues

If all checks pass, the tag can be created with:
```bash
./scripts/create_tag.sh vX.Y.Z-rc1
```
