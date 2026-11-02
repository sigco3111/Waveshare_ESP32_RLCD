# Syna 1.0.0-rc.2 (release candidate)

Windows Reporter and installer self-tests passed; standalone application BIN and full BIN completed local flashing and read-back verification, confirmed by the user.

Applies to Waveshare ESP32-S3-RLCD-4.2, 16 MB Flash, 8 MB PSRAM.

## This release's features

- Displays computer performance, Agent status and quota, and music information.
- LAN discovery and selection of computers.
- Windows graphical installer supporting Reporter installation, configuration-preserving upgrade, and first-time install; backs up before flashing and verifies after writing.
- One wake-up per question/answer round; voice interruption is not accepted while answering (voice testing pending).

## Installation

Open `SynaInstaller-1.0.0.exe`; if compatible firmware is already present, choose "configuration-preserving upgrade"; if only the computer side is needed, choose "Reporter only".

"First-time install" clears board data. Do not unplug during flashing; after completion confirm screen light-up and network connection; if the screen does not light up, unplug and replug and press the power button after all verification is complete.

## Files

| File | Purpose |
| --- | --- |
| `SynaInstaller-1.0.0.exe` | Windows all-in-one installer |
| `SynaReporter.exe` | Standalone computer-side program |
| `xiaozhi.bin` | Application firmware; cannot be written as a full image at address 0 |
| `Syna-source-1.0.0.zip` | Project source and build documentation |
| `third-party-sources/`, `LICENSES/` | Third-party source and license materials, distributed with the program |
| `SHA256SUMS.json` | File checksum manifest |

## Current status

Windows local installation, configuration-preserving upgrade, screen light-up, network connection, binding preservation, and performance data display have been accepted. Voice and another Windows test remain pending; macOS was not re-validated this round.

Music progress is an estimate. The Windows package is not code-signed. Full acceptance and release preparation status: [Release checklist](RELEASE_CHECKLIST.md).

When reporting feedback, provide system version, installation mode, and error information; do not publish full Flash backups or logs containing credentials.

Xiaozhi network setup, activation, and role settings: [Xiaozhi setup guide](XIAOZHI_SETUP.md).
