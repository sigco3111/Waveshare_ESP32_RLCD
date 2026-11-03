#!/bin/bash
# Keep the Reporter running inside the GUI login session.
#
# launchd starts this watchdog. The watchdog launches the Reporter through
# the GUI session, because macOS applies the local network privacy control
# per process: a Reporter running in the launchd background session receives
# LAN packets but cannot send to a peer on the local network, so the panel
# never receives the discovery reply.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
LAUNCHER="$HERE/start_background.command"
LOG="$HOME/Library/Application Support/SynaReporter/keep-alive.log"

while true; do
  if ! pgrep -f "reporter\.py --no-supervisor" >/dev/null 2>&1; then
    /usr/bin/open "$LAUNCHER" >> "$LOG" 2>&1
    echo "Relaunched the Reporter at $(date)" >> "$LOG"
    # Give the new process time to bind its ports before the next check.
    sleep 15
  else
    sleep 20
  fi
done
