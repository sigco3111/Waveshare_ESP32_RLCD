# Mac One-Click Installer

Copyright (c) 2026 Heimu. Installer original code uses the project MIT license.

`Installer.swift` provides a native AppKit window; `worker.py` handles release file verification, device backup,
partition detection, flashing, and atomic Reporter replacement. PyInstaller bundles Python and esptool together,
so installation requires no dependency downloads.

## Build

Prepare Python 3.12, Xcode Command Line Tools, a verified
Reporter `.app`, and an ESP-IDF firmware build directory on an Apple Silicon Mac. Building does not flash devices.

```bash
python3.12 -m venv .codex-tmp/installer-venv
.codex-tmp/installer-venv/bin/pip install -r installer/macos/requirements-build.txt
.codex-tmp/installer-venv/bin/python installer/macos/build.py \
  --worker-python .codex-tmp/installer-venv/bin/python \
  --firmware-build /path/to/xiaozhi/build \
  --reporter-app reporter/dist-macos/SynaReporter.app
```

Default toolchain and firmware paths follow this project's local conventions. The build also reads the corresponding ESP-IDF LICENSE,
firmware dependency directories, and licenses from Reporter's `.venv-macos`; prepare the project environment first if any are missing.
Python runtime licenses, dependency licenses, and font attributions are all collected into Payload/Legal.

The release private key is at `~/Library/Application Support/SynaReleaseSigning/private.pem`,
and is not included in the installer. The public key uses `release/keys/syna-release-public.pem`, whose SHA-256
is pinned inside the worker. When changing signing identity, sync the public key fingerprint and notify users through official channels.

Output: `release/artifacts/v1.0.0-macos-installer/`, containing the DMG, user guide, and signature manifest.
The installer does not yet use Developer ID signing or Apple notarization; do not describe the project release signature as Apple certification.

## Verification

```bash
python3.12 -m unittest discover -s installer/macos -p 'test_*.py' -v
python3 release/sign_release.py verify release/artifacts/v1.0.0-macos-installer
```

Tests cover OTA dual-partition selection, damaged partition/OTA records, wrong board model, link escape, install file
changes, backup verification failure blocking writes, first-install backup ordering, and refusing to overwrite unrelated apps.
Actual install check records are in `VERIFICATION.md`. User operations are in [User Guide](USER_GUIDE.md).
