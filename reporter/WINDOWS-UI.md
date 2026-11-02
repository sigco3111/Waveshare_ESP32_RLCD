# Windows status window

Copyright (c) 2026 Heimu. Original code uses MIT.

`windows_ui.py` uses PySide6 Essentials and ports the 760 x 750 layout of
`native_ui.swift`, the card positions, colors, copy and author information to
Windows; Qt scales with the system DPI.
The font is Segoe UI, with Chinese falling back to Microsoft YaHei UI / Microsoft YaHei. The Mac app is unchanged.
When the workspace is small the window shrinks automatically and provides scrolling, keeps the original 760x750 content layout, and the bottom actions stay reachable.

## Usage

On Windows run `start.ps1`, or double-click the newly built `dist/SynaReporter.exe`.
Starting with no arguments shows the status window; `--worker`, `--self-test`, `--no-supervisor` and other command-line behaviors are preserved.

- The status queries the local HTTP asynchronously every second; stale values are cleared after a disconnect. Unsupported sensors show `—`.
- It can start and stop the service it created; when an external process provides the service, only the data is shown.
- Closing the window hides it to the system tray; clicking the tray icon or opening the program again shows the window; the tray menu can quit.
- The worker is restarted with backoff when it ends unexpectedly; an explicit stop and quit do not trigger a restart.
- Start at Login uses the current user's Run registry key and does not require the window to run as administrator.
- When an old HKLM startup item is detected, it prompts to run the new installer first, to avoid the switch showing off while the program still starts automatically.
- The About Author dialog contains Heimu, Bilibili UID 386856267, QQ 3091479711, the version and the Official Repository / Release Download links.

The install script has been changed to remove the old HKLM startup item and set HKCU instead; the ownership of an elevated install under a different administrator account,
and the problem of uninstalling other users' startup items, need to be verified and refined in the later Windows all-in-one installer.

## Verified and pending

2026-09-13: In a standalone Python 3.12 / PySide6 Essentials 6.8.3 environment on the Mac,
the interface offscreen rendering was completed and manually checked; 7 tests passed, covering real subprocess start and stop, crash recovery,
external process protection, missing metrics, disconnect cleanup and registry simulation tests. The asynchronous request to the existing Reporter
interface succeeded, and the existing Mac service was neither started nor stopped.

The above is the historical record of September 13; the Windows progress is in the supplement below.

### 2026-09-14 Windows on-machine verification

- Environment: Windows x64, Python 3.11.9, PySide6 Essentials 6.8.3; a new Windows virtual environment has been created.
- Backup before the changes: `Backup_Windows_Before_On-Machine_Verification_20260914_102730/`, keeping the old EXE, the installer package and the original Reporter.
- Fixed the problem where the fixed-size window exceeded the workspace at high scaling, and made the Chinese fallback font explicit; the old computer name is also cleared when the service is disconnected.
- The Reporter regression suite has 46 tests in total: 33 passed, 13 macOS-only tests skipped; the window tests number 8.
- The local 1920x1080 screen displays correctly; `QT_SCALE_FACTOR=1/1.5/2` verified that the window stays inside the workspace at all three scale factors, and that the bottom controls are reachable after scrolling. This is not equivalent to acceptance of an actual system DPI switch or a multi-monitor setup.
- The source window was tested against a real worker and HTTP, close to tray, a second launch recalling the original window without duplicating the worker, recovery after a crash, clearing data after a stop, restart, and a clean exit with no leftover worker.
- The HKCU autostart value was tested on and off and restored to its pre-test value; the Author dialog content and both link targets are correct, and the external sites were not actually opened.
- The new EXE has been built and passes `--self-test`; its window, the real background HTTP, tray hiding and a repeated launch recalling the window were tested.
- CPU/GPU/memory/disk and the CPU/GPU temperatures have data on this machine, and the weekly quota has data; the short-window quota stays `—` when it is missing.
- Both the source and the new EXE received a discovery request from 1 board; this cannot replace the user's confirmation that the board has selected this computer and that the screen shows it correctly. NetEase Cloud Music playback joint debugging is not complete yet.

The current new program: `dist/SynaReporter.exe`, 41,895,786 bytes (about 40 MiB).
SHA-256: `eac0c514f55d1dd97b44914d445ca95dd512976f782b2c3e336c741119b9edd6`.

**`release/SynaReporter-Setup-1.0.0.exe` is still the old installer package from September 5 and does not contain the new window.**
This round delivers the locally runnable new EXE first; the install script's cross-administrator-account ownership, uninstall/upgrade and the Qt distribution license still need to be handled, and the old installer package cannot be presented as this round's output.

Pending acceptance: an actual system DPI switch, multiple monitors, tray mouse interaction, disabling the startup entry in Task Manager, re-login/reboot, sleep recovery, long-running operation, the board screen and NetEase Cloud Music playback, and install/upgrade/uninstall.
The local temporary test scripts, JSON results, screenshots and build logs are in `.codex-tmp/` and are not part of the public release content.

```powershell
python -m unittest discover -s reporter -p test_windows_ui.py -v
powershell -ExecutionPolicy Bypass -File reporter/build_release.ps1 -Version 1.0.0
```

Qt/PySide retain their own separate licenses; see THIRD_PARTY_NOTICES.md in the root directory.
