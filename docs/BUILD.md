# Build guide

The following commands are run from the project root. Verification results: [build record](BUILD_VALIDATION.md).

## Reporter

Use Python 3.11. On Windows, run from the project root:

```powershell
python -m venv reporter/.venv
reporter/.venv/Scripts/python.exe -m pip install -r reporter/requirements-build.txt
Push-Location reporter
.venv/Scripts/python.exe -m PyInstaller --noconfirm --distpath dist --workpath build SynaReporter.spec
Pop-Location
```

Output is `reporter/dist/SynaReporter.exe`. The source run entry is `reporter/reporter.py`; the Mac build entry is `reporter/build_macos.command`.

## ESP-IDF firmware

1. Install Git, ESP-IDF **6.0.2**, and the ESP32-S3 toolchain; activate the official ESP-IDF environment.
2. Check out the repository specified by `xiaozhi/upstream.lock` at the locked commit and initialize submodules. Windows source and build paths should use space-free ASCII paths.
3. Install `xiaozhi/requirements-firmware.txt` in the activated environment.
4. Run `python <project>/xiaozhi/apply_ui_overlay.py <upstream> --phase source`.
5. In the upstream directory, run the following commands to resolve components, apply component patches, then build:

```powershell
idf.py -DIDF_TARGET=esp32s3 '-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;syna.sdkconfig.defaults' -DBOARD_NAME=esp32-s3-rlcd-4.2 reconfigure
python <project>/xiaozhi/apply_ui_overlay.py <upstream> --phase components
python scripts/build.py waveshare/esp32-s3-rlcd-4.2 --name esp32-s3-rlcd-4.2 --language en-US
```

`<project>` and `<upstream>` are paths to replace. Output is in the upstream `build` directory. `build_windows.ps1` is a convenience wrapper for the author's existing tool directory layout; prefer the manual entry points above for general environments. `build_macos.sh` accepts the upstream path and `SYNA_IDF_ROOT`.

## Windows all-in-one installer

Complete the Reporter and firmware builds first, then run:

```powershell
reporter/.venv/Scripts/python.exe -m pip install esptool==5.4.0
reporter/.venv/Scripts/python.exe installer/windows/build_standalone.py --firmware-build C:/syna/xiaozhi/build --reporter-exe reporter/dist/SynaReporter.exe
```

Replace `C:/syna/xiaozhi/build` with the firmware output directory. Installer output is in `installer/windows/dist`.

After preparing the payload, run `python -m unittest -v test_installer.py` in `installer/windows`. Tests use PySide6; firmware host tests additionally need a C++ compiler, with path settings in the script headers.

Firmware host tests can set `SYNA_FIRMWARE_SOURCE` to the patched upstream source and `SYNA_VCVARS` to Visual Studio's `vcvars64.bat`.

## Simulator

Requires CMake, SDL2, and LVGL **9.5.0**. Place that version's full source in `simulator/vendor/lvgl-9.5.0`, retain the original license, and build with `simulator/CMakeLists.txt`. Font sources and licenses are retained with the source; the Python font generator is recommended. The PowerShell simulator scripts still contain the author's local paths; adjust them before use, or configure the SDL2 search path directly through CMake.
