# Syna v1.0.0-rc.2 standalone BIN flashing

Applies only to Waveshare ESP32-S3-RLCD-4.2: ESP32-S3, 16 MB Flash, 8 MB PSRAM.

## First-time install / replacing other firmware
File: Syna-1.0.0-rc.2-full-16MB.bin (16 MB)
Write address: 0x0
Contains the bootloader, partition table, OTA initialization data, application, and screen resources.
The full image overwrites all Flash and clears Wi-Fi, computer binding, and other device configuration. Back up first; do not unplug during flashing.

Example using esptool 5.4.0 (replace COM9 with your own board's serial port):
python -m esptool --chip esp32s3 --port COM9 --baud 921600 --after hard-reset write-flash --flash-mode dio --flash-freq 80m --flash-size 16MB 0x0 Syna-1.0.0-rc.2-full-16MB.bin

Other flashing tools: select ESP32-S3, DIO, 80 MHz, 16 MB, and place the full BIN at address 0x0.

## Application image (advanced use)
File: Syna-1.0.0-rc.2-app.bin
This is a standalone application; it does not include the bootloader, partitions, or resources, cannot be written to 0x0, and cannot be used for first-time installation on a blank device.
The default build application address is 0x20000; an existing device may boot from another OTA partition, so that address cannot simply be assumed.
Use this only after confirming device partitions, the current boot slot, and resource compatibility, and after handling OTA boot selection yourself. Configuration-preserving upgrades should prefer the graphical installer.

## Verification and boot
The BIN comes from the same firmware batch as the rc.2 installer. The application hash, the full image's five sections, and the padding regions have been verified. Both application BIN configuration-preserving upgrade and full BIN first-time install succeeded in real testing on the author's device, and the full image's 16 MB read-back matches the release file.
Wait for boot after the flashing tool reports completion; if the screen does not light up, unplug and replug and press the power button. Wi-Fi and computer binding must be reconfigured.
BIN-SHA256SUMS.txt contains the checksums for these standalone BINs and this note. It does not install the computer-side Reporter; install that separately when computer data is needed.
## Xiaozhi voice configuration

1. After the board's first boot, follow the on-screen prompts to connect to the device hotspot, open the prompted configuration page, and set an available Wi-Fi. Computer binding and Wi-Fi setup are completed on the device page.
2. Open https://xiaozhi.me/ in a browser, sign in, and enter the "Console".
3. If the device shows or announces an activation code, add the device in the console as prompted, enter the current activation code, and bind it to your own account or agent. For an already bound device, look it up under the original account first; clearing Flash does not necessarily remove the cloud binding.
4. In the agent associated with the device, open "Configure role", set the role persona, voice, and the model options provided on the page, save, then test by waking again; restart the device if it does not take effect.
5. The Xiaozhi console is used for voice conversation configuration; computer performance, Agent, and music data require the computer-side Reporter, and the computer must also be selected on the board.

If there is no activation code, first confirm the device is already online. Devices that can already converse normally usually do not need reactivation; console entry names are as actually shown on the web page.
