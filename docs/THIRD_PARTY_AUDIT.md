# Third-Party Distribution Audit (2026-09-16)

## Verified and Supplemented

- Recorded 39 Python distribution packages from the validation environment. This number is an environment manifest; it does not claim that every package entered the final EXE.
- Read three PyInstaller Analysis manifests, recording the Reporter, installer, and backend modules, binaries, and data files; not just requirements.txt.
- The actual Qt dynamic libraries include Core, Gui, Widgets, Network, and Svg; same-package platform and image plugins must also be considered.
- Found that the Qt wheel metadata only includes the commercial license, so the original packer missed the LGPL/GPL text. LGPLv3, GPLv3, and GPLv2 were supplemented from the Qt 6.8.3 upstream.
- Supplemented the upstream licenses for pyserial 3.5 and PyWinRT 3.2.1, plus the CPython runtime LICENSE.
- Collected licenses for 177 configured components from the ESP-IDF build description. Configured components do not all contribute final linked code, so this list is a conservative collection, not a per-symbol SBOM.
- Confirmed ESP-SR 2.4.7 and mn7_cn/fst from the actual configuration and build logs; recorded 6 model file hashes.
- The Reporter spec and installer build scripts now integrate the supplementary materials above and the source acquisition notes, preventing future builds from depending only on wheel metadata.

Machine-readable record: THIRD_PARTY_AUDIT.json; license materials: `release/licenses/windows-audit/`; collection script: `release/audit_licenses.py`. All files come from a clearly versioned upstream or the actual build environment; original licenses are not rewritten.

## Subsequent Material Supplements

Versioned source packages for Qt Base, SVG, imageformats, PySide/Shiboken, esptool, Mesa, LLVM, and OpenSSL have been obtained, and the Qt attributions plus the original licenses they reference have been parsed. Materials and hashes are recorded in THIRD_PARTY_SOURCE_ARCHIVES.json. Source packages, the project source ZIP, and license notes will be provided together with the candidate release directory; final artifacts and verification results are in RELEASE_CANDIDATE.json.

Qt modules use a conservative collection scope that includes example/test declarations that may not enter the current binary. It must not be claimed that all listed third parties are used by the current program.

## Still to Verify for Formal Distribution

1. Confirm that the corresponding source, original license, and project build materials are all provided with the final package, not only the EXE.
2. A modified-Qt actual rebuild has not been performed; the existing scripts provide a rebuild route, and verified compatible library replacement is not claimed.
3. The publisher's applicable license for the Microsoft VC Runtime must be verified by the author; the existing installation environment cannot substitute for authorization confirmation, see RUNTIME_NOTICES.md.
4. The Mesa/LLVM version was verified from the actual DLL, but vendor patches and build options were not independently reproduced; source and limitations are retained.
5. Fonts have source records; image assets follow the author's earlier confirmation and have not yet been re-archived file by file.

## Reference Basis

- Qt for Python third-party notice: https://doc.qt.io/qtforpython-6.8/licenses.html
- Qt 6.8.3 LGPLv3 text: https://raw.githubusercontent.com/qt/qtbase/v6.8.3/LICENSES/LGPL-3.0-only.txt
- esptool 5.4.0: https://github.com/espressif/esptool/blob/v5.4.0/LICENSE
- pyserial 3.5: https://raw.githubusercontent.com/pyserial/pyserial/v3.5/LICENSE.txt
- PyWinRT 3.2.1: https://raw.githubusercontent.com/pywinrt/pywinrt/v3.2.1/LICENSE

No changes were made to the development directory this time, and nothing was installed, flashed, or uploaded. The conclusion is "license collection gaps were found and patched; clear distribution TODOs remain", not "all third parties have been reviewed and approved".
