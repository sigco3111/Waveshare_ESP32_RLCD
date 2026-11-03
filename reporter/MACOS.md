# macOS Reporter Guide

This round completed the basic macOS adaptation of the computer-side Reporter, reusing the existing V1 UDP protocol of the board.
No board firmware change is needed to connect a Mac. Actual screen display and cross-device discovery still require integration testing with the board.

## Startup

Recommended: double-click `dist-macos/SynaReporter.app` to open the native Mac status window directly.
You can also double-click `start.command` in this directory: it opens the same window when a built application is detected.
The window shows the service status, CPU/memory/disk usage, network speed, Codex status and quota, and the most recently received board requests, refreshed every second.
"Stop Service" / "Start Service" control the background process started by this window; "Diagnostics" opens the read-only endpoint, and "Open Logs" locates the log directory.
Closing the window keeps the service running in the background; click the Dock icon or press Command+0 to show it again. Command+Q quits and stops the services it manages.
If the service was started by another process, the window only shows its status and does not end that process on its own.
You can also run it from the terminal:

```bash
cd "/path/to/project/reporter"
./start.command
```

A built `.app` bundles its own runtime, so no separate Python installation is needed. If no application has been built, the start script uses Python 3.9+ to create `.venv-macos` in this directory, install the dependencies, and run in terminal mode.
`.venv-macos` has been created and verified on this machine. When running from source on another Mac without Python, install Python 3.9+ first; the interpreter can be selected with `SYNA_PYTHON=/absolute/path/python3 ./start.command`.

After startup, open `http://127.0.0.1:8765/api/v1/status` to view the data and `http://127.0.0.1:8765/api/v1/health` to check the service status.
The computer and the board must be on the same mutually reachable Wi-Fi; allow Reporter local network access when the system asks.
Do not forward the diagnostic endpoint or the UDP port to the internet.

## Currently Supported Scope

| Feature | macOS base version |
| --- | --- |
| UDP 8766 discovery, stable computer identity, binding fingerprint | Implemented, local protocol tests pass; integration testing with the board pending |
| CPU, memory, disk, upload/download speed | Measured on an Apple Silicon Mac |
| Disk usage | Reads the APFS data volume `/System/Volumes/Data` first, to avoid counting only the read-only system volume |
| Codex process and local state | Mac process names supported; the database only queries the existing status fields and workspace path |
| Codex login and quota | Queried through app-server; compatible with the keychain login managed by Codex itself |
| NetEase Cloud Music | Connected to the normally started Mac client: song, artist, play/pause, real progress, total duration, and lyrics |
| Music data source | Mac reads the system Now Playing; the existing Windows CDP/local read path is kept |
| GPU utilization, CPU/GPU temperature | Verified working on Apple M5, no administrator rights needed; returns `null` when unavailable |
| Background recovery, single instance, logging | Implemented; an optional user-level launchd management script is also provided |

When no reliable music data is available, `media.available=false` is returned and the device shows "Not playing" following the existing logic.
This means no usable data was obtained; it cannot be used to judge whether NetEase Cloud Music on the Mac is actually playing.
The Windows local cache path is not used on Mac, and playback progress is never fabricated.

The Codex status now primarily reads the fixed-format `turn/started`/`turn/completed` lifecycle markers in `logs_2.sqlite`, and combines the process PID and creation time to exclude exited clients and PID reuse. Multiple clients and parallel tasks within the same client are supported.
After all tasks finish, "Done" is shown for about 120 seconds, then the state returns to "Idle". The lifecycle records contain no reliably associated workspace name, so this data source shows the generic `Codex` name.
The SQL returns only timestamps, process identifiers, and fixed event types; it does not return log bodies, prompts, replies, or tool arguments.
If the read fails or the client provides no such markers, it falls back to the previous history table/process check. This log format is a version-dependent implementation, not a guaranteed stable external API; it may need matching changes after a client update or a log cleanup.
For the account actually used here, only the weekly quota window is returned; the short window stays `--` and missing quota is not estimated.

## NetEase Cloud Music on Mac

Just open NetEase Cloud Music normally and play a song; no debug port is needed. The Reporter window shows the song, the artist, play/pause and progress; the board keeps using the existing `media_*` fields to display the music and the current lyrics, so no firmware update is required.
Reads happen about once per second and follow the progress computed by the system; pausing, seeking, and track changes are all re-corrected.

The implementation runs read-only Foundation/AppKit/MediaRemote queries through the macOS built-in `osascript`. It does not drive the player UI, does not use System Events, does not read cookies, accounts, or playback history, and does not modify the NetEase Cloud Music client. Only the current system player with bundle ID `com.netease.163music` is accepted.
If the current system media switches to a browser or another player, it reports unavailable; play in NetEase Cloud Music again to recover.
When NetEase Cloud Music is not running, the system provides no track, or the interface fails, the old song is cleared.

MediaRemote is a private interface, verified on this machine with macOS 26.6.2 and NetEase Cloud Music 3.1.8. Compatibility with all macOS/NetEase Cloud Music versions is not promised, and it must be re-verified after a system upgrade.
API call reference: [MRNowPlayingRequest example](https://gist.github.com/SkaplanOfficial/f9f5bdd6455436203d0d318c078358de).

Lyrics reuse the existing NetEase Cloud Music search and LRC lookup: the current song title and artist are sent to the NetEase Cloud Music interface to match the song, without sending account credentials. The query runs in the background and does not block the live playback state; with no network, no match, or no lyrics, "No lyrics" is shown. Cover art and remote playback control are not provided at this time.

## Apple Silicon GPU and Temperature

GPU utilization is read from the IORegistry key `AGXAccelerator / PerformanceStatistics / Device Utilization %` and updated every second; Renderer and Tiler counts are not added on top, to avoid double counting.
CPU temperature is the average of the valid `Tp*` and `Te*` sensors, and GPU temperature is the average of `Tg*`, updated every 5 seconds. These are sensor group averages and do not represent the hottest point or the case temperature.
The SMC probe only performs read operations: it does not write to SMC and does not change fan, power, or thermal control settings.
No sudo, administrator password, or additional privacy permission is required.

Verified working on this machine with Apple M5 / macOS 26.6.2. Sensor names and the ABI are not a stable public Apple protocol; see the [mactop SMC implementation](https://github.com/metaspartan/mactop/blob/main/internal/app/smc.c).
Other chips and OS versions need separate verification; when no sensor matches, the read times out, or the data is invalid, `--` is shown and stale temperature values are not reused.
The application already includes `MacThermalProbe`; if it is missing when running from source, only the temperature is unavailable and it can be compiled first:

```bash
mkdir -p .macos-tools
clang -O2 -Wall -Wextra -framework IOKit macos_thermal.c -o .macos-tools/MacThermalProbe
```

## Packaging

An Apple Silicon build has been produced: `dist-macos/SynaReporter.app`.
It contains a native Swift / AppKit status window plus the Python Reporter backend.
Double-clicking it opens the window and starts the service; if a service is already running, its live status is shown directly.
The page clearly shows running / stopped / disconnected; on disconnect the old values are cleared, so cached numbers are not mistaken for live data.
The board communication field only means that discovery requests were received in the last 15 seconds; it does not mean the board has selected this machine.
The local package uses ad-hoc signing and has not gone through Developer ID signing or notarization; it is not a finished public release package.

Run either from source or from the `.app`. Clicking "Stop Service" in the window stops the collection and keeps the window open; quitting the application also stops the background process it started. Force-killing the worker triggers recovery by the background supervisor.

Rebuild:

```bash
./build_macos.command
```

The output uses the architecture of the build machine; an Intel Mac needs to be rebuilt and verified in a matching environment, and compatibility with all Macs is not claimed at this time.

## Auto-start at Login

Turn on "Start at Login" at the bottom of the app window (macOS 13+ required). The switch reads the real system state; once enabled, the next login to the current Mac account opens the app window and starts the Reporter; turning it off does not affect the running service.
If it shows "Waiting for system permission", click "Login Items" to go to the system settings and allow it; after a change in the system settings, the window syncs automatically.
Closing the window still keeps it running; Command+Q only ends the current run and does not cancel the next-login auto-start.
Keep the app in a fixed location; re-check the switch after moving or replacing it. The actual log out / log in effect has to be verified at a convenient time.
The implementation uses Apple's [SMAppService](https://developer.apple.com/documentation/servicemanagement/smappservice).

### Advanced: the legacy background-only script

This script and the window switch are two independent mechanisms; do not enable both at once. If the script was installed before, run `macos_service.py uninstall` first and then use the window switch. Users who only need the background service without a window can stop the manually started Reporter and then run:

```bash
.venv-macos/bin/python macos_service.py install
.venv-macos/bin/python macos_service.py status
```

This registers the service for the current user in `~/Library/LaunchAgents/local.syna.reporter.plist`, letting launchd start and recover the worker without administrator rights.
The service uses the absolute paths of the current project and virtual environment; do not move the project after installation, and run install again if it is moved.
Access to the Desktop directory is managed by macOS; if the background start is rejected by the system, check the service log and the system privacy settings.

```bash
.venv-macos/bin/python macos_service.py stop       # stop this run, still starts at next login
.venv-macos/bin/python macos_service.py start      # start again
.venv-macos/bin/python macos_service.py uninstall  # stop and remove the login start, keep config and logs
```

#### Why the service runs a watchdog instead of the Reporter directly

macOS applies the local network privacy control per process. A Reporter that launchd starts in the background session can receive LAN packets but cannot send to a peer on the local network: every send fails with `ENETUNREACH` (errno 65). The panel discovers the Reporter by UDP broadcast and only connects when the reply comes back, so in that state the service looks healthy on HTTP `8765` while every panel stays offline and the screen keeps the last values.

The service therefore registers `keep_alive.command`, a watchdog that stays alive under launchd and launches the Reporter through the GUI login session with `open`, which keeps the local network permission of that session. The watchdog re-launches the Reporter when it is gone, so a crash is recovered within about 30 seconds.

The launchd plist parameters have been tested; user login, auto-start, system permission dialogs, and sleep/wake still need verification in a real environment.

## Configuration, Logs, and Codex Paths

Default directory: `~/Library/Application Support/SynaReporter/`.
`reporter.json` holds the stable computer identity and binding information, and `reporter.log` is the rotating log.
Do not delete the configuration file, otherwise the device treats it as a new Reporter.
launchd standard output is recorded separately as `launchd.stdout.log` and `launchd.stderr.log`.

- `SYNA_REPORTER_DATA_DIR`: overrides the data directory, which is useful for isolated testing.
- `SYNA_CODEX_EXECUTABLE`: sets the absolute path of the Codex executable.
- `CODEX_HOME`: follows the Codex data directory setting.

The program searches PATH first, then the common Codex.app / CLI locations, and then the Mac executable inside the VS Code extension.
The VS Code extension path on this Mac has been verified. After a Codex update the path changes; reinstalling the background service refreshes its fixed path.
The Mac login state is determined by `account/read` and does not read authentication files or keychain contents directly; quota is obtained through `account/rateLimits/read`.

## Verification

```bash
.venv-macos/bin/python -m unittest discover -v
SYNA_TEST_APP="$PWD/dist-macos/SynaReporter.app/Contents/MacOS/SynaReporter" \
  .venv-macos/bin/python -m unittest test_macos.MacProtocolTests -v
```

The tests use a temporary configuration and check the HTTP and UDP of a real child process, identity consistency across two starts, clean exit, and port release. If UDP 8766 is already taken by the Reporter, the protocol test is skipped; stop the running program first.

Board acceptance: discover the Mac → select the Mac → verify the performance data → verify the Codex status and quota → stop/restart the Reporter → disconnect/restore Wi-Fi → Mac sleep/wake.

## Engineering Boundaries

This round did not modify or flash the firmware in `src/` or `xiaozhi/overlay/`, and did not migrate all development tools.
The Windows build directory in `platformio.ini`, `xiaozhi/apply-ui-overlay.ps1`, the simulator's Windows build script, and the System.Drawing-based font/image generation scripts are kept unchanged.
They do not affect using the existing firmware with the Mac Reporter in this round; rebuilding the whole firmware and resources on Mac would require separate toolchain migration and verification.

Backup before the adaptation: `backup_before_mac_adaptation_20260909_130845/` in the project root; after the copy, 9,803 files were verified with SHA-256.

References: [psutil support matrix](https://psutil.readthedocs.io/stable/index.html), [PyInstaller packaging documentation](https://pyinstaller.org/en/stable/usage.html), [Apple launchd documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html).
