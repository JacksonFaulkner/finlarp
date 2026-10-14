#!/bin/sh
# Install (or with `uninstall`, remove) the launchd agents that run jobs.refresh.
#   sh py/jobs/launchd/install.sh            # daily + intraday
#   sh py/jobs/launchd/install.sh daily      # just one
#   sh py/jobs/launchd/install.sh uninstall
# Run one now: launchctl kickstart gui/$(id -u)/com.finlarp.refresh.daily
set -eu
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
agents="$HOME/Library/LaunchAgents"
logs="$HOME/.local/share/nvim/finlarp/logs"
uv=$(command -v uv)
dom="gui/$(id -u)"

if [ "${1:-}" = uninstall ]; then
  for m in daily intraday; do
    launchctl bootout "$dom/com.finlarp.refresh.$m" 2>/dev/null || true
    rm -f "$agents/com.finlarp.refresh.$m.plist"
  done
  echo "removed"
  exit 0
fi

mkdir -p "$agents" "$logs"
for m in ${1:-daily intraday}; do
  dst="$agents/com.finlarp.refresh.$m.plist"
  sed -e "s|__UV__|$uv|" -e "s|__ROOT__|$root|" -e "s|__LOGS__|$logs|" "$here/com.finlarp.refresh.$m.plist" > "$dst"
  plutil -lint "$dst" >/dev/null
  launchctl bootout "$dom/com.finlarp.refresh.$m" 2>/dev/null || true
  launchctl bootstrap "$dom" "$dst"
  echo "loaded com.finlarp.refresh.$m  (log: $logs/launchd-$m.log)"
done
