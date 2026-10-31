#!/bin/bash
# PostToolUse hook (async, asyncRewake): after Claude edits a Rust file under
# tui/, rebuild the `fl` release binary in the background and wake Claude when
# done. Exit 2 is how an async hook wakes the model; the message on stderr is
# what Claude reads.
#
# Builds are coalesced: if a build is already running, this call only marks
# the tree dirty and the running build does one more pass before it reports.
# The Claude session is a separate tmux session, so rebuilding does not touch it.

set -u

TUI_DIR="/Users/jacksonfaulkner/code/github_repos/finlarp/tui"
LOCK_DIR="$HOME/.cache/finlarp/fl-build.lock"
DIRTY="$HOME/.cache/finlarp/fl-build.dirty"
LOG="$HOME/.cache/finlarp/fl-build.log"
CHANGED="$HOME/.cache/finlarp/fl-build.changed"

input=$(cat)
# Pause switch: `touch ~/.cache/finlarp/fl-build.paused` silences rebuilds during bulk edits.
[ -e "$HOME/.cache/finlarp/fl-build.paused" ] && exit 0
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

case "$file" in
  "$TUI_DIR"/*.rs) ;;
  *) exit 0 ;;
esac

printf '%s\n' "${file#"$TUI_DIR"/}" >> "$CHANGED"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  # Another build owns the lock; it will pick up this edit on its next pass.
  touch "$DIRTY"
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

status=0
while :; do
  rm -f "$DIRTY"
  (cd "$TUI_DIR" && cargo build --release) > "$LOG" 2>&1
  status=$?
  [ -e "$DIRTY" ] || break
done

changed=$(sort -u "$CHANGED" 2>/dev/null | paste -sd ' ' -)
rm -f "$CHANGED"

if [ "$status" -eq 0 ]; then
  echo "fl rebuilt OK (edited: ${changed:-unknown}). Move the user to the screen that shows the change with fl-show." >&2
else
  echo "fl build FAILED (edited: ${changed:-unknown}). Last lines of $LOG:" >&2
  tail -n 40 "$LOG" >&2
fi
exit 2
