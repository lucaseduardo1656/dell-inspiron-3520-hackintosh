#!/bin/bash
# lid-guard: this laptop only has S0ix (Modern Standby) and macOS never completes
# sleep on it ("System sleep prevented by kPMPCIUnsupported"), so a closed lid
# leaves the machine running and heating up with no airflow. Instead:
#   lid closed            -> Low Power Mode on (restored when the lid opens)
#   closed > LIDGUARD_SHUTDOWN_AFTER s -> graceful shutdown, forced after a grace period
# Clamshell use with an external display (AppleClamshellCausesSleep = No) is left alone.
# Runs as root from /Library/LaunchDaemons/local.lidguard.plist.
SHUTDOWN_AFTER="${LIDGUARD_SHUTDOWN_AFTER:-900}"   # 15 min
FORCE_AFTER="${LIDGUARD_FORCE_AFTER:-180}"         # extra wait before forcing
POLL=5
DRYRUN="${LIDGUARD_DRYRUN:-0}"                    # 1 = only log the actions

run() { if [ "$DRYRUN" = 1 ]; then log "[dry-run] $*"; else "$@"; fi; }
log() { echo "$(date '+%F %T') $*"; }
prop() { ioreg -r -k AppleClamshellState -d 1 | awk -F'= ' -v k="\"$1\"" '$0 ~ k {gsub(/ /,"",$2); print $2; exit}'; }
lowpower() { pmset -g | awk '/lowpowermode/ {print $2; exit}'; }

# WhateverXe eDP wake bug: the internal panel's link training sometimes fails when
# the display wakes (black screen, cursor still visible). Another display
# sleep/wake cycle retrains the link, so retry up to 3 times.
panel_failed() {
  /usr/bin/log show --last "${1}s" --style compact --predicate 'process == "kernel"' 2>/dev/null |
    grep -qE "link training failed|Hardware mode set failed"
}
recover_panel() {
  sleep 4
  local i
  for i in 1 2 3; do
    panel_failed 8 || return 0
    log "panel did not come back (link training failed): display cycle $i"
    run pmset displaysleepnow; sleep 3
    run caffeinate -u -t 2; sleep 4
  done
  panel_failed 8 && log "panel still failing after 3 cycles"
}

closed_since=0; saved_lpm=""; asked_at=0; forced=0
log "started (shutdown after ${SHUTDOWN_AFTER}s closed)"
while true; do
  state=$(prop AppleClamshellState); causes=$(prop AppleClamshellCausesSleep)
  now=$(date +%s)
  if [ "$state" = "Yes" ] && [ "$causes" = "Yes" ]; then
    if [ "$closed_since" -eq 0 ]; then
      closed_since=$now; saved_lpm=$(lowpower)
      [ "$saved_lpm" = "1" ] || run pmset -a lowpowermode 1
      log "lid closed: low power mode on (was ${saved_lpm:-?})"
    fi
    if [ $((now - closed_since)) -ge "$SHUTDOWN_AFTER" ]; then
      if [ "$asked_at" -eq 0 ]; then
        asked_at=$now
        user=$(stat -f %Su /dev/console); uid=$(id -u "$user" 2>/dev/null)
        log "lid closed for $((now - closed_since))s: asking $user's session to shut down"
        if [ -n "$uid" ] && [ "$user" != "root" ]; then
          run launchctl asuser "$uid" sudo -u "$user" osascript -e 'tell application "loginwindow" to «event aevtrsdn»' >/dev/null 2>&1
        else
          run shutdown -h now
        fi
      elif [ "$forced" -eq 0 ] && [ $((now - asked_at)) -ge "$FORCE_AFTER" ]; then
        forced=1
        log "graceful shutdown did not finish in ${FORCE_AFTER}s: forcing"
        run shutdown -h now
      fi
    fi
  elif [ "$closed_since" -ne 0 ]; then
    [ "$saved_lpm" = "1" ] || run pmset -a lowpowermode "${saved_lpm:-0}"
    log "lid opened after $((now - closed_since))s: low power mode restored to ${saved_lpm:-0}"
    closed_since=0; saved_lpm=""; asked_at=0; forced=0
    recover_panel
  fi
  sleep "$POLL"
done
