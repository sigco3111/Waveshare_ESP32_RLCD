# Syna · Mac Installer Package v1.0.0

Author: Heimu · Bilibili UID 386856267 · QQ 3091479711

Compatible hardware: Waveshare ESP32-S3-RLCD-4.2 (16 MB Flash).
Mac: Apple Silicon, minimum declared system macOS 13; currently tested on this Mac's macOS 26.
Intel Mac is not included in this installer package. Installation requires no Python, ESP-IDF, or administrator password.

## Usage

1. Open the DMG and double-click **SynaInstaller.app**.
2. Connect the board with a USB cable that supports data transfer, then click "Refresh devices".
3. If the board already uses this project's firmware, choose "Preserve-config upgrade (recommended)"; for a new board or replacing other firmware, choose "Fresh install / replace other firmware", read and check the data-erasure confirmation. You can also choose "Reporter only".
4. Click "One-click install" and wait for backup, verification, flashing, and Reporter installation to complete. Do not unplug or close the computer during this time.
5. Reporter opens automatically. Put the computer and the board on the same mutually reachable Wi-Fi, then follow the board prompts to provision Wi-Fi and select the computer.

If the serial port cannot connect: hold BOOT, reinsert USB, release BOOT, then retry.
PWR is short-press to power on and long-press to power off; after installing a battery you may need to connect USB once to activate.
Closing the Reporter window does not exit the service; Command+Q exits. Login auto-start can be adjusted in the Reporter window.
When the system asks for local network, music automation, or similar permissions, allow them as needed for the features you want.

## Backup and Upgrade

- Reporter installs to `~/Applications/SynaReporter.app`; computer-side settings remain in the original Application Support directory.
- When upgrading an existing app, the old Reporter moves to this backup directory. Running Reporter exits normally during installation.
- The device's full Flash is read and verified before writing; on failure, flashing does not continue.
- Backups and logs: `~/Library/Application Support/SynaInstaller/Backups/`, openable directly from the installer.
- **Device backups contain private configuration such as Wi-Fi and activation; do not upload or share them publicly.**
- Preserve-config mode requires a partition layout compatible with this model and recognizes the existing board model and boot partition; on incompatibility, writing is refused.
- First install erases board data, but the original full backup is saved and verified first.
- On failure, check the log and retry; if flashing completed but Reporter installation failed, switch to "Reporter only".

## Source and Signature

Official repository: https://github.com/heimumumu/Waveshare_ESP32_RLCD

Release page: https://github.com/heimumumu/Waveshare_ESP32_RLCD/releases

The installer verifies the embedded release signature and file hashes before installing. The DMG also includes `SHA256SUMS.json` and
`SHA256SUMS.sig`, verifiable with `release/sign_release.py verify <download directory>` from the repository.
The public key should be checked against a trusted official channel; do not trust the source solely because the public key ships with the file.

The current app uses only local ad-hoc code signing, **with no Apple Developer ID signing or Apple notarization**.
macOS may block it when downloaded from the internet; after confirming the official source, choose "Open Anyway" in "System Settings → Privacy & Security".
Do not disable Gatekeeper globally. The project release signature verifies author origin and cannot replace Apple notarization.

The original parts use MIT; third-party code, models, and fonts keep their own licenses. Licenses are in the installer's
`Contents/Resources/Payload/Legal`. Do not describe the entire firmware uniformly as MIT.
