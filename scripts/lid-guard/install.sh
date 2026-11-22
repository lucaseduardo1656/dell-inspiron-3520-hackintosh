#!/bin/bash
# Install or remove lid-guard. Run with sudo:
#   sudo scripts/lid-guard/install.sh            install / update
#   sudo scripts/lid-guard/install.sh --remove   uninstall and restore Low Power Mode off
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run with sudo" >&2; exit 1; }
DIR="$(cd "$(dirname "$0")" && pwd)"
BIN=/usr/local/libexec/lid-guard.sh
PLIST=/Library/LaunchDaemons/local.lidguard.plist

launchctl bootout system "$PLIST" 2>/dev/null || true
if [ "${1:-}" = "--remove" ]; then
  rm -f "$BIN" "$PLIST"
  pmset -a lowpowermode 0
  echo "lid-guard removed"; exit 0
fi
install -d -m 755 /usr/local/libexec
install -m 755 -o root -g wheel "$DIR/lid-guard.sh" "$BIN"
install -m 644 -o root -g wheel "$DIR/local.lidguard.plist" "$PLIST"
launchctl bootstrap system "$PLIST"
sleep 1
launchctl print system/local.lidguard | grep -E "state =|pid =" || true
tail -n 2 /var/log/lidguard.log 2>/dev/null || true
echo "lid-guard installed; log: /var/log/lidguard.log"
