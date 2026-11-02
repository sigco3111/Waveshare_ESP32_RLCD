# Syna

Waveshare ESP32-S3-RLCD-4.2 desktop assistant, with the Windows / macOS Reporter companion.

Current version: **1.0.0 release candidate**.

## Features and supported scope

- The board displays computer performance, Agent status and quota, and music information.
- LAN discovery of computers, selection of the bound computer, configuration preserved across upgrades.
- The Windows all-in-one installer offers three modes: Reporter-only, configuration-preserving upgrade, and first-time install.
- The current firmware uses one wake-up per question/answer round; voice interruption is not accepted while answering. This has been compiled and flashed; the actual voice experience still needs validation.
- Music timing uses the current estimation logic; precise real-time progress is not guaranteed.

The hardware target is ESP32-S3-RLCD-4.2, with 16 MB Flash and 8 MB PSRAM. Do not flash the firmware to other models.

## Usage

After official release, get the matching system installer from the project Releases. This source directory does not include installers, runtime environments, or device configuration.

For Windows users, after opening the installer: if the board already has this project's firmware, choose "configuration-preserving upgrade"; if only the computer side is needed, choose "Reporter only". "First-time install" clears the board's existing data; confirm before proceeding. Keep the USB connection during flashing and keep backups until acceptance is complete.

Windows computer-side installation and configuration-preserving flashing have been accepted by the author on their own machine. macOS has an independent implementation with prior validation, but it has not been re-validated against this round of Windows changes.

## Xiaozhi voice configuration

1. After the board's first boot, follow the on-screen prompts to connect to the device hotspot, open the prompted configuration page, and set an available Wi-Fi. Computer binding and Wi-Fi setup are completed on the device page.
2. Open https://xiaozhi.me/ in a browser, sign in, and enter the "Console".
3. If the device shows or announces an activation code, add the device in the console as prompted, enter the current activation code, and bind it to your own account or agent. For an already bound device, look it up under the original account first; clearing Flash does not necessarily remove the cloud binding.
4. In the agent associated with the device, open "Configure role", set the role persona, voice, and the model options provided on the page, save, then test by waking again; restart the device if it does not take effect.
5. The Xiaozhi console is used for voice conversation configuration; computer performance, Agent, and music data require the computer-side Reporter, and the computer must also be selected on the board.

If there is no activation code, first confirm the device is already online. Devices that can already converse normally usually do not need reactivation; console entry names are as actually shown on the web page.

More details: [Xiaozhi setup guide](docs/XIAOZHI_SETUP.md).

## Source layout

| Directory | Contents |
| --- | --- |
| `xiaozhi/` | Patches, board-level source, and ESP-IDF build entry for the pinned Xiaozhi upstream version |
| `reporter/` | Computer-side status service, media collection, Windows / Mac UI |
| `installer/` | Windows / Mac installer source |
| `simulator/` | LVGL UI simulator, assets, and font generator |
| `tests/` | Host tests for firmware UI and status logic |
| `release/` | Release signing tools, public key, and third-party licenses |

Firmware is based on **ESP-IDF 6.0.2**.

Build entry points: [Build guide](docs/BUILD.md); known limitations: [Release checklist](docs/RELEASE_CHECKLIST.md).

Version contents: [Release notes](docs/RELEASE_NOTES_1.0.0.md).

## Author and license

Author: Heimu. Original parts are distributed under [MIT](LICENSE); third-party code, fonts, and models keep their original licenses, see [Third-party notices](THIRD_PARTY_NOTICES.md).

Repository: <https://github.com/heimumumu/Waveshare_ESP32_RLCD>


