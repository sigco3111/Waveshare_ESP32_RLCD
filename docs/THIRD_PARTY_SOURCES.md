# Third-Party Sources and Rebuild

This project uses Qt/PySide6, esptool, and other third-party software. The MIT license of the original source does not change third-party licenses; do not call the whole installer and its contained dependencies MIT.

| Component | Verified Version | Corresponding Source Entry |
| --- | --- | --- |
| Qt Core/Gui/Widgets/Network, platform plugins | 6.8.3 | https://github.com/qt/qtbase/tree/v6.8.3 |
| Qt SVG | 6.8.3 | https://github.com/qt/qtsvg/tree/v6.8.3 |
| Qt imageformats plugins | 6.8.3 | https://download.qt.io/archive/qt/6.8/6.8.3/submodules/ |
| PySide6 / Shiboken6 | 6.8.3 | https://github.com/qt/pyside-setup/tree/v6.8.3 |
| esptool | 5.4.0 | https://github.com/espressif/esptool/tree/v5.4.0 |
| pyserial | 3.5 | https://github.com/pyserial/pyserial/tree/v3.5 |
| PyWinRT (runtime/Foundation/Collections/Media.Control) | 3.2.1 | https://github.com/pywinrt/pywinrt/tree/v3.2.1 |
| CPython | 3.11.0 | https://github.com/python/cpython/tree/v3.11.0 |
| PyInstaller | 6.21.0 | https://github.com/pyinstaller/pyinstaller/tree/v6.21.0 |
| ESP-IDF | 6.0.2 | https://github.com/espressif/esp-idf/tree/v6.0.2 |
| OpenSSL (CPython DLL) | 1.1.1q | https://github.com/openssl/openssl/tree/OpenSSL_1_1_1q |
| Mesa / LLVM (opengl32sw.dll) | 11.2.2 / 3.6.2 | https://archive.mesa3d.org/older-versions/11.x/11.2.2/ and https://releases.llvm.org/3.6.2/ |

More dependency versions are in `release/build-info/windows-validation-20260916/`; release metadata, license files, and source URLs are in `docs/THIRD_PARTY_AUDIT.json`. These entries locate the source; providing links alone does not satisfy the final binary source distribution requirements.

## Source Provided with the Candidate Package

The candidate release directory's `third-party-sources/` actually provides versioned upstream source archives for Qt Base, SVG, imageformats, PySide/Shiboken, esptool, Mesa, LLVM, and OpenSSL, not just download links. Per-package URL, size, and SHA256 are in `SOURCE_ARCHIVES.json`; licenses and attributions are extracted verbatim from these archives into `release/licenses/upstream-source-notices/`. The project's application source is placed separately in `Syna-source-1.0.0.zip`.

Qt's officially released module source packages and the GitHub tag source are used to preserve the corresponding version. The Mesa/LLVM version was verified from the actual DLL's embedded version string; it cannot be claimed that all build options or vendor patches of this prebuilt DLL have been fully reproduced.

## Qt and Modified Libraries

Qt/PySide6 uses open-source licenses; commercial authorization is not claimed based on the commercial license text that ships with the wheel. The LGPLv3 text and the GPLv3 text it references are included in `release/licenses/windows-audit/supplemental/Qt-6.8.3/`.

The project does not prohibit users from debugging, reverse engineering, replacing, or rebuilding the program in order to modify third-party libraries. Syna's Python, install backend, and packaging scripts are provided as source.

Recombination route: install dependencies at locked versions in an independent Python environment, install a self-built compatible PySide6/Shiboken6/Qt into that environment, then build the Reporter and installer according to `docs/BUILD.md`. PySide build reference: https://doc.qt.io/qtforpython-6.8/building_from_source/index.html . Do not assume library replacement has been verified by modifying a one-time temporary extraction directory.

The current single-file artifact has not yet been rebuilt with a modified Qt; the publisher still needs to choose and implement how the corresponding source and recombination materials are delivered. The final release must carry the license and ensure that the corresponding source and build materials are actually obtainable.

When releasing this candidate directory, the application source package, the third-party source above, and the build instructions should be provided together, and an accessible download location should be kept. Do not upload only the EXE and then claim the corresponding source is already included. The modified-Qt rebuild has not yet been performed, and the related limitations must be retained.

## esptool

esptool's GPLv2-or-later remains in effect; its bundled stubs carry separate Apache/MIT files, all of which are retained. The backend invokes the flashing functionality in a subprocess, but the backend program itself also packages and imports esptool, so no GPL distribution obligation can be dismissed merely by "using a subprocess". At release, the corresponding esptool source, this project's backend source, the dependencies, and the build instructions should be provided together, and the distribution method of the final release combination should be verified.

## Models and Fonts

The actual configured models for ESP-SR 2.4.7 are `mn7_cn` and `fst`. `THIRD_PARTY_AUDIT.json` records the original model file hashes; the models are not this project's original work, and their license includes the Espressif product usage scope. Font sources and hashes are in `simulator/assets/fonts/SOURCE.md`, keeping the OFL/original COPYING.

This is a distribution engineering record; see THIRD_PARTY_AUDIT.md for uncompleted items. It does not mean the final package is fully approved for release.
