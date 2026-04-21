#!/usr/bin/env bash
set -e

# Run tests inside Docker before committing

if [ ! -f "Dockerfile" ]; then
    exit 0
fi

# Only run when source, test, or build files are staged
STAGED=$(git diff --cached --name-only --diff-filter=AM | grep -E '(^src/|^tests/|^Dockerfile$|^requirements\.txt$)' || true)

if [ -z "$STAGED" ]; then
    exit 0
fi

echo "🐳 Building Docker image and running tests..."

if ! docker build -t kata-tests-precommit . -q > /dev/null 2>&1; then
    echo "❌ Docker build failed. Fix the build before committing."
    exit 1
fi

if ! docker run --rm kata-tests-precommit; then
    echo "❌ Tests failed inside Docker. Fix tests before committing."
    exit 1
fi

echo "✅ All tests passed."
