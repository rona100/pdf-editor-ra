#!/usr/bin/env bash
# Stop: when Python files differ from HEAD, run the backend suite before
# Claude ends its turn, and send it back to fix any failure (exit 2).
#
# The suite takes ~30s, so a passing run is remembered by a hash of the
# Python changes and not repeated until they change again.
set -u

input=$(cat)
# Already continuing because of this hook: don't loop.
[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

changes=$( { git diff HEAD -- '*.py'; git ls-files --others --exclude-standard -- '*.py' | xargs -r cat; } 2>/dev/null )
[ -n "$changes" ] || exit 0

stamp=.claude/.last-green-tests
hash=$(printf '%s' "$changes" | sha256sum | cut -d' ' -f1)
[ -f "$stamp" ] && [ "$(cat "$stamp")" = "$hash" ] && exit 0

if out=$(.venv/bin/pytest -q -x -p no:cacheprovider 2>&1); then
  echo "$hash" > "$stamp"
  exit 0
fi

printf 'Backend tests fail with the current changes. Fix them before finishing:\n%s\n' "$(printf '%s' "$out" | tail -40)" >&2
exit 2
