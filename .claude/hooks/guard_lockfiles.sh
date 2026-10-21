#!/usr/bin/env bash
# PreToolUse(Edit|Write): lockfiles are generated; editing them by hand
# produces a lock that no longer matches what the resolver would write.
file=$(jq -r '.tool_input.file_path // empty')
case "$file" in
  */uv.lock|uv.lock)
    echo "Do not edit uv.lock by hand. Change pyproject.toml and run 'uv lock' (or 'uv add' / 'uv remove')." >&2
    exit 2 ;;
  */package-lock.json|package-lock.json)
    echo "Do not edit package-lock.json by hand. Change frontend/package.json and run 'npm install' in frontend/." >&2
    exit 2 ;;
esac
exit 0
