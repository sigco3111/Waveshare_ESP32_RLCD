# Windows All-in-One Installer

Source entry installer_ui.py, backend protocol worker.py, standalone backend entry backend_entry.py. The release directory does not carry Payload, generated manifest, or EXE.

Build instructions: [unified guide](../../docs/BUILD.md). build_standalone.py must provide --firmware-build and --reporter-exe; prepare_payload.py accepts the same two parameters and can prepare test files separately.

After generation run dist/SynaInstaller-1.0.0.exe. Read-only self-test command: SynaInstaller-1.0.0.exe --self-test <absolute report path.json>, does not install or flash.

Three modes: Reporter-only install, preserve-config upgrade, first install. Reporter-only does not access serial ports; upgrade backs up and verifies partitions, writes only the app; first install requires confirmation to erase, erases only after full backup verification. Read-back verification and reset at the end. Failure does not auto-rollback; keep backups.

Backend uses ASCII JSON escaping to pass messages, avoiding Windows code page errors; final success requires both completion event and normal exit.

Currently the author's standalone Reporter install and preserve-config flashing verified successfully; rebuild in a new directory, another PC, first install, and voice testing still need verification. Backups in %LOCALAPPDATA%/SynaInstaller/Backups contain private data; do not commit to the source repository.
