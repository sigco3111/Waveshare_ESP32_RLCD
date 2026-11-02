# 1.0.0 local candidate release package

These artifacts are pre-release review materials: not uploaded, not signed. On 2026-09-16, local Reporter installation, configuration-preserving flashing, and independent read-back verification were completed; the user confirmed normal screen light-up, automatic network connection, preserved computer binding, and continuous performance data refresh (see HARDWARE_ACCEPTANCE.json). This is not an officially released version.

## Contents

- Windows all-in-one installer and standalone Reporter, rebuilt and passed read-only self-test.
- Firmware application image (not a full Flash image).
- Project source ZIP, including build scripts, version records, and documentation.
- 42 versioned upstream source distribution packages, about 165 MB, including Qt/PySide, esptool, and Python dependencies.
- Qt's 67 attributions and the licenses they reference; all references have been located.
- `LICENSES/`, third-party notices, and per-file `SHA256SUMS.json`.

Machine-readable artifact hashes and self-test evidence: RELEASE_CANDIDATE.json. Both Reporter and installer verified the embedded 444 license materials file by file; their content matches the current source directory.

## Reproduction flow

1. Build according to BUILD.md; in the validation environment run `release/collect_source_archives.py --python-sources --output <source package directory>` to collect the corresponding distribution packages.
2. In the validation environment run `release/verify_candidate.py --validation-root <validation directory>`; this process does not install or flash.
3. Run `release/assemble_candidate.py --validation-root <validation directory> --output <new empty directory>`.

The source collection script reads fixed versions from Qt's official release directory, project upstream, and PyPI. PyPI source packages are also compared against their release metadata SHA256. Qt/GitHub downloads record SHA256 for later verification; download records are not claimed as publisher digital signatures.

## Items retained before release

Local installation, configuration-preserving upgrade, and the above runtime checks have passed; this does not mean all functions are accepted. Single-turn voice, first-time clearing install, and another Windows test remain. RELEASE_CANDIDATE.json keeps the build-time read-only self-test record; later on-device results are in HARDWARE_ACCEPTANCE.json. Documentation inside existing candidate packages is a packaging-time snapshot; updated documentation and hash manifests must be re-aggregated before official release.

Recombination testing after modifying Qt is not yet complete; applicability of Microsoft VC Runtime redistribution is to be verified by the author. Mesa/LLVM have only had version and source verified, not independent rebuild of vendor DLLs. Image sources follow the author's prior confirmation.

At official release, programs, project source, and third-party source materials should be provided together, not just a single EXE. The SHA256 manifest is for integrity verification and does not represent source signatures or satisfaction of all release conditions.
