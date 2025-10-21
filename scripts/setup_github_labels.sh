#!/bin/bash
# Setup GitHub labels for issue tracking
# Creates labels for bugs, features, AI process failures, and categories

set -e

echo "Setting up GitHub labels..."

# Type Labels (mutually exclusive - pick one)
gh label create "bug" \
  --description "Something isn't working" \
  --color "d73a4a" \
  --force || true

gh label create "enhancement" \
  --description "New feature or request" \
  --color "a2eeef" \
  --force || true

gh label create "documentation" \
  --description "Improvements or additions to documentation" \
  --color "0075ca" \
  --force || true

gh label create "ai-process" \
  --description "AI process failure (mistake in workflow/architecture)" \
  --color "7057ff" \
  --force || true

gh label create "question" \
  --description "Further information is requested" \
  --color "d876e3" \
  --force || true

# AI Process Categories (use with ai-process label)
gh label create "missing-docs" \
  --description "Documentation not updated" \
  --color "fef2c0" \
  --force || true

gh label create "missing-tests" \
  --description "Tests not written or updated" \
  --color "fbca04" \
  --force || true

gh label create "missing-automation" \
  --description "Automation opportunity missed" \
  --color "f9d0c4" \
  --force || true

gh label create "architecture-violation" \
  --description "Violated architectural principles" \
  --color "e99695" \
  --force || true

gh label create "tdd-violation" \
  --description "Did not follow TDD workflow" \
  --color "d93f0b" \
  --force || true

gh label create "other" \
  --description "Other category (use when specific category doesn't fit)" \
  --color "ededed" \
  --force || true

# Severity Labels (optional, use for bugs and ai-process)
gh label create "critical" \
  --description "Critical priority" \
  --color "b60205" \
  --force || true

gh label create "high" \
  --description "High priority" \
  --color "d93f0b" \
  --force || true

gh label create "medium" \
  --description "Medium priority" \
  --color "fbca04" \
  --force || true

gh label create "low" \
  --description "Low priority" \
  --color "0e8a16" \
  --force || true

# duplicate label (GitHub provides by default, but ensure it exists)
gh label create "duplicate" \
  --description "This issue is a duplicate of another issue" \
  --color "cfd3d7" \
  --force || true

echo ""
echo "✅ GitHub labels created successfully!"
echo ""
echo "Labels created:"
echo "  Type: bug, enhancement, documentation, ai-process, question"
echo "  AI Categories: missing-docs, missing-tests, missing-automation, architecture-violation, tdd-violation, other"
echo "  Severity: critical, high, medium, low"
echo "  Other: duplicate"
