# ESP-IDF Firmware

The current implementation applies board-level source and single-turn conversation patches to the Xiaozhi upstream pinned by `upstream.lock` via `apply_ui_overlay.py`.

Unified build steps are in [Build Guide](../docs/BUILD.md). Both Windows and Mac use the Python overlay script; the old PowerShell overlay script is not included in this organized directory to avoid two patch sets drifting out of sync.

`build_windows.ps1` and `enter-idf.ps1` keep default values for the author tool directory layout and can be adjusted via parameters; if an official ESP-IDF 6.0.2 environment already exists, use the manual commands in the build guide instead of reusing the author directories.

Board: waveshare/esp32-s3-rlcd-4.2, 16 MB Flash, 8 MB PSRAM. Back up and verify partitions before upgrading.

Single-turn conversation: automatic sentence segmentation by default; voice processing and wake-word detection are disabled during the reply; returns to idle after TTS ends and local playback completes. Manual stop via button is retained; microphone gain is unchanged by this round of changes. Compiled and flashed; voice real-world testing is still pending.
