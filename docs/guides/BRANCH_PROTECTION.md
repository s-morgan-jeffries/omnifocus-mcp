# Branch Protection Configuration

This document explains how to configure GitHub branch protection for the `main` branch.

**Status:** Required for v0.6.4+ (release branch workflow)

## Why Branch Protection?

With release branches, main branch must be protected to:
1. **Prevent direct pushes** - All changes go through PRs (even from maintainers)
2. **Require CI to pass** - Hygiene checks must succeed before merge
3. **Prevent force pushes** - Can't rewrite main history
4. **Prevent deletion** - Can't accidentally delete main branch

## Configuration Steps

### Via GitHub Web UI

1. Go to: `https://github.com/s-morgan-jeffries/omnifocus-mcp/settings/branch_protection_rules/new`

2. **Branch name pattern:** `main`

3. **Protect matching branches** - Enable these settings:

   **Require a pull request before merging:**
   - ✅ Enabled
   - ❌ Require approvals: 0 (solo development - can self-merge)
   - ❌ Dismiss stale PR approvals: Not needed initially
   - ❌ Require review from Code Owners: Not needed (no CODEOWNERS file)

   **Require status checks to pass before merging:**
   - ✅ Enabled
   - ✅ Require branches to be up to date before merging
   - **Required status checks** (add these):
     - `validate-prevention-measures` (if CI workflow exists)
     - `test` or `tests` (main test workflow)
     - Any other critical CI jobs

   **Require conversation resolution before merging:**
   - ❌ Optional (nice to have but not critical)

   **Require signed commits:**
   - ❌ Not required (adds complexity)

   **Require linear history:**
   - ✅ Enabled (prevents merge commits, enforces squash/rebase)
     - Alternative: Leave disabled if you prefer merge commits

   **Do not allow bypassing the above settings:**
   - ✅ Enabled (even admins must follow rules)
     - Alternative: Disable if you need emergency override capability

   **Rules applied to administrators:**
   - ✅ Enabled (maintainers follow same rules)

   **Restrictions:**
   - ❌ Not needed (no team-based access control)

   **Allow force pushes:**
   - ❌ DISABLED (never allow force push to main)

   **Allow deletions:**
   - ❌ DISABLED (never allow deleting main)

4. Click **Create** or **Save changes**

### Via GitHub CLI

```bash
# Note: gh CLI doesn't fully support branch protection configuration
# Use web UI for initial setup, then can view with CLI:

gh api repos/s-morgan-jeffries/omnifocus-mcp/branches/main/protection
```

### Via API

```bash
# Full configuration via API (adjust as needed):
curl -X PUT \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/s-morgan-jeffries/omnifocus-mcp/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["tests", "validate-prevention-measures"]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "required_approving_review_count": 0,
      "dismiss_stale_reviews": false
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "required_linear_history": true
  }'
```

## Verification

After configuration, verify protection is active:

```bash
# Try to push directly to main (should fail):
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "test: verify protection"
git push origin main
# Expected: remote: error: GH006: Protected branch update failed

# Verify protection settings:
gh api repos/s-morgan-jeffries/omnifocus-mcp/branches/main/protection
```

## Impact on Workflow

**What changes:**
- ❌ Can't `git push origin main` anymore
- ✅ Must create PRs for all main updates
- ✅ CI must pass before merge allowed
- ✅ Can still push to feature/release branches normally

**Release workflow:**
1. Work on `release/v0.6.x` branch (no protection)
2. Create PR: `release/v0.6.x` → `main`
3. CI runs on PR
4. Merge PR (via GitHub UI or `gh pr merge`)
5. Main branch updated via PR (not direct push)

**Feature workflow:**
1. Work on `feature/description` branch
2. Create PR: `feature/description` → `main`
3. CI runs, must pass
4. Merge PR

## Minimal Configuration (Start Here)

If unsure, start with minimal protection:

```
✅ Require pull request (0 approvals needed)
✅ Require status checks (list critical checks)
✅ Require branches up to date
✅ Block force pushes
✅ Block deletions
❌ Everything else disabled initially
```

Can tighten later as workflow matures.

## Troubleshooting

**Problem:** Can't merge PR - "Required status check X has not run"

**Solution:**
- Check if status check name matches exactly
- Verify GitHub Actions workflow is configured to run on PRs
- May need to remove check from required list temporarily

**Problem:** Emergency hotfix needed but can't push to main

**Solution:**
1. Disable "Do not allow bypassing" temporarily (requires admin)
2. Push hotfix
3. Re-enable protection immediately after

## Future Enhancements

When external contributors appear:
- Require 1 approval for PRs
- Add CODEOWNERS file
- Require conversation resolution
- Add team-based restrictions

## References

- GitHub Docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches
- Issue #55: Define contributor workflow and enable branch protection
- Issue #62: Implement release branches and protect main branch
