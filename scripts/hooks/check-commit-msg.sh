#!/usr/bin/env bash
# Validates conventional commit format: #<issue> <type>(<scope>): <description>

MSG_FILE="$1"
MSG=$(head -1 "$MSG_FILE")

# Allow merge and revert commits
if echo "$MSG" | grep -qE "^(Merge|Revert) "; then
    exit 0
fi

# Match: #N type(scope): description
if echo "$MSG" | grep -qE "^#[0-9]+ (feat|fix|docs|test|refactor|chore|ci|perf|style)\([a-z0-9-]+\): .+$"; then
    exit 0
fi

echo "❌ Invalid commit message format."
echo "   Expected: #<issue> <type>(<scope>): <description>"
echo "   Example:  #1 feat(auth): add login endpoint"
echo "   Types: feat, fix, docs, test, refactor, chore, ci, perf, style"
exit 1
