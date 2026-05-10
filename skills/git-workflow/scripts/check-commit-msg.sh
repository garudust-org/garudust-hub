#!/usr/bin/env bash
# Validate a commit message against the conventional commits format.
# Usage: check-commit-msg.sh "feat(auth): add login"
set -euo pipefail

msg="${1:-}"
if [[ -z "$msg" ]]; then
  echo "Usage: check-commit-msg.sh <message>" >&2
  exit 1
fi

pattern='^(feat|fix|docs|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .{1,72}$'

if echo "$msg" | grep -qE "$pattern"; then
  echo "OK: '$msg'"
else
  echo "FAIL: '$msg' does not follow conventional commits format." >&2
  echo "Expected: <type>(<scope>): <summary>" >&2
  exit 1
fi
