# Syna Reporter (Windows / macOS)

The macOS base version is adapted: double-click `start.command` to start, or use `dist-macos/SynaReporter.app`. Feature scope, start-at-login and testing are covered in [macOS usage notes](MACOS.md). The Windows status window has been ported from the Mac layout; the first round of on-machine Windows verification was completed on 2026-09-14 and a new `dist/SynaReporter.exe` was built. Usage and the remaining verification items are in [Windows window notes](WINDOWS-UI.md). NetEase Cloud Music, the NVIDIA metrics and the installation method below apply to Windows.

The current main entry point on Windows is the all-in-one installer in `installer/windows`, and the standalone install has been accepted on the author's own machine. The tidied source directory does not include a prebuilt EXE; generate it following the [build instructions](../docs/BUILD.md).

To run the current local build directly:

```text
dist\SynaReporter.exe
```

The path below is the output of the retained standalone Reporter packaging script; it is not the entry point of this unified release:

```text
release\SynaReporter-Setup-1.0.0.exe
```

The installed single-file program bundles the Python runtime and all dependencies and starts automatically at login after installation; if the worker managed by the window exits abnormally it is recovered automatically, and the explicit command-line background mode keeps the supervisor. The installer only adds an inbound rule for UDP 8766 on the Private network. Developers start from source:

```powershell
powershell -ExecutionPolicy Bypass -File .\reporter\start.ps1
```

The first run creates an isolated Python environment in `reporter/.venv` and installs `psutil` and the Windows Runtime media interface. The Reporter listens on:

- HTTP `8765`: `/api/v1/health`, `/api/v1/status`
- UDP `8766`: responds to `AI_PANEL_DISCOVER_V1`, and also returns the computer identity, the Agent status and a performance snapshot

The stable `reporter_id` and the computer name are stored in `%LOCALAPPDATA%\AIAgentPanel\reporter.json`.

On the first start the Reporter also generates a random pairing token and fingerprint. A new board automatically stores the stable Reporter ID and fingerprint found on first discovery, so the user does not need to copy any token; the manual token is only for legacy firmware compatibility or advanced filtering. The local diagnostic endpoint `http://127.0.0.1:8765/api/v1/pairing` still allows local access only and never returns a plaintext token to the LAN.

The current version exposes read-only status endpoints only; it does not read prompts, code, file contents or API keys. If Windows shows a firewall prompt during the first LAN test, allow the Private network only.

The board and the computer must be on the same Wi-Fi or phone hotspot that lets devices reach each other. After a successful start, check in a browser on the computer:

```text
http://127.0.0.1:8765/api/v1/health
http://127.0.0.1:8765/api/v1/status
```

The current MVP performance data includes CPU, Memory, GPU and Disk usage, GPU temperature and real-time network speed. When Windows has no generally reliable CPU temperature interface, the value is `null` and the screen shows `--`. NVIDIA GPU metrics come from `nvidia-smi`; without an NVIDIA GPU the GPU item shows `--`.

## Codex Agent status

The Reporter first extracts fixed-format task start/end markers from the Codex local `logs_2.sqlite`, and combines the process PID and creation time to aggregate the number of live activities; it does not read or report the log body. That log format depends on the client version. When no marker is available, it falls back to a read-only query of the `thread_turns` state in `thread_history_1.sqlite` and takes the matching workspace name from `state_5.sqlite`. While an `inProgress` turn exists, the status shows "Working"; after the most recent turn completes, "Done" is shown for a short time; when the Codex process exists but no turn is active, the status shows "Idle"; when the process exits, the status shows "Not running". When several Codex sessions run at the same time, `active_count` returns the number of active sessions.

This approach does not depend on a VS Code Hook and does not read `thread_items`, prompts, conversations, code, tool arguments or terminal output. Over UDP the Reporter sends the screen only the aggregate status, the active count and the last path segment of the workspace name.

The official installed version no longer uses VBS. The installer writes a system startup item that starts a hidden supervisor; the run log is at `%LOCALAPPDATA%\AIAgentPanel\reporter.log`. It is independent of the VS Code process, so `Developer: Reload Window` is no longer required for status synchronization.

## Codex quota

Every 30 seconds the Reporter reads the account limits through `account/rateLimits/read` on the local Codex App Server, converts `usedPercent` into the remaining percentage, and distinguishes the short-window quota from the weekly quota by `windowDurationMins`. The data is sent to the screen over UDP together with the computer status; when a window has no reliable data, the screen shows `--`, and no fixed value or local token consumption estimate is used.

This uses the Codex client that is already signed in on the current computer, calls the read-only limit endpoint only, and does not read authentication tokens, prompts, conversations or code. If the local App Server protocol changes after a Codex client upgrade, the Reporter adapter must be updated accordingly.

When Codex is not signed in, the Reporter immediately clears the old quota and reports the state that requires a login; the screen shows "Please log in" and both quota items show `--`. After a successful sign-in, the values come back no later than the next 30-second poll.

## NetEase Cloud Music and lyrics

The Reporter first reads the NetEase Cloud Music song title, artist, playback state and real progress directly from a local CDP channel that listens on `127.0.0.1:9223` only; older clients can still use the Windows `GlobalSystemMediaTransportControlsSessionManager`. When newer builds such as NetEase Cloud Music 3.1.39 disable the Windows media session, the Reporter reads the current song, artist, song ID and duration read-only from the window title and the local `playingList`, so a normal shortcut launch does not lose the whole media block. For precise progress, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\reporter\start_netease_precise.ps1 -Restart
```

The script first fully exits the existing NetEase Cloud Music process, then starts it in precise mode and verifies that the port is really available; a failed verification reports the error clearly, so the "looks like it started successfully but there is actually no media information" case no longer happens. After manually quitting NetEase Cloud Music, start it with this script from then on.

When the song changes, the Reporter first parses candidate song IDs from the NetEase Cloud Music local cache file names and then validates them strictly against the song title and artist; only when no cache match is found does it call the NetEase Cloud Music search endpoint. Lyrics are matched to the current playback position by LRC timestamp; when the network is unavailable, the song has no lyrics or no reliable match exists, the screen shows "No lyrics" and lyrics from a same-titled cover song are never applied. The song ID and lyrics are cached until the next track change, so normal playback does not repeatedly request the network.

The home screen font covers common Chinese characters, Japanese hiragana, katakana, half-width katakana and JIS kanji, so Chinese and Japanese song titles, artists and single lyric lines can be shown dynamically. Only the NetEase Cloud Music desktop client is supported at present. If NetEase Cloud Music is not running, has just restarted and has not loaded a song yet, or is not playing, the screen shows "Not playing".

The ESP32 live data link uses UDP request/response, so no Windows TCP inbound rule is needed for HTTP `8765`; the HTTP endpoints are only a local diagnostic entry. Do not open firewall permissions for public networks, and do not set up port forwarding on the router.

The board supports discovering up to 8 Reporters, paging through the list, selecting the current computer, and locking the current selection by stable Reporter ID and remembered fingerprint; the board itself uses its Wi-Fi STA MAC as a stable ID. This mechanism is meant to avoid cross-wiring between multiple computers and boards; it is not equivalent to protection against malicious LAN attacks. Bidirectional message authentication with a random nonce and a revocation list are still to be added in later security hardening. The Agent status and quota are now connected to Codex; media and lyrics currently support only the NetEase Cloud Music desktop client.

Build the release package:

```powershell
powershell -ExecutionPolicy Bypass -File .\reporter\build_release.ps1 -Version 1.0.0
```
