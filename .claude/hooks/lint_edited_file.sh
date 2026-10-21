#!/usr/bin/env bash
# PostToolUse(Edit|Write): lint the file Claude just changed and hand any
# problem the linter could not fix back to Claude (exit 2 = feedback).
#
# Python gets `ruff check --fix` (lint only, no reformatting: the codebase
# is not ruff-formatted, and formatting on touch would bury real diffs).
# TypeScript gets a project-wide `tsc --noEmit`, which takes a few seconds.
set -u

file=$(jq -r '.tool_input.file_path // empty')
[ -n "$file" ] && [ -f "$file" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

case "$file" in
  *.py)
    ruff_bin=$(command -v ruff || echo "uvx ruff")
    out=$($ruff_bin check --fix --quiet "$file" 2>&1) || {
      printf 'ruff found problems it could not fix in %s:\n%s\n' "$file" "$out" >&2
      exit 2
    }
    ;;
  */frontend/src/*.ts|*/frontend/src/*.tsx|frontend/src/*.ts|frontend/src/*.tsx)
    out=$(cd frontend && npx --no-install tsc --noEmit 2>&1) || {
      printf 'TypeScript errors after editing %s:\n%s\n' "$file" "$(printf '%s' "$out" | grep -v '^npm notice' | head -40)" >&2
      exit 2
    }
    ;;
esac
exit 0
