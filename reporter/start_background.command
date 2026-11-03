#!/bin/bash
# Start the Reporter inside the GUI login session.
#
# macOS applies the local network privacy control per process. A Reporter
# started by launchd in the background session cannot send to a peer on the
# local network (every send fails with ENETUNREACH), so the panel never
# receives the discovery reply and the screen keeps showing stale data.
# Launching through the GUI session keeps the local network permission.
set -uo pipefail
cd "$(dirname "$0")"
LOG="$HOME/Library/Application Support/SynaReporter/gui-session.log"
mkdir -p "$(dirname "$LOG")"
if pgrep -f "reporter\.py --no-supervisor" >/dev/null 2>&1; then
  echo "Reporter already running: $(pgrep -f 'reporter\.py --no-supervisor' | tr '\n' ' ')" >> "$LOG"
  exit 0
fi
PY=./.venv-macos/bin/python
[[ -x "$PY" ]] || PY=/opt/homebrew/bin/python3
nohup "$PY" reporter.py --no-supervisor >> "$LOG" 2>&1 &
disown
echo "Reporter started from GUI session at $(date)" >> "$LOG"
