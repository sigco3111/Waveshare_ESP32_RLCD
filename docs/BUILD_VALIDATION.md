# 2026-09-16 independent source rebuild

Verification directory: `D:/syna-release-validation-20260916`, separate from the development directory and the open-source preparation directory. Only documentation and test script parameters were revised in the open-source preparation directory; the original development source was not modified, and neither Reporter was installed nor the board flashed.

## Isolation scope

- Source copied from the open-source directory, with a fresh Python 3.11 virtual environment and declared dependencies installed.
- The locked Xiaozhi commit was independently cloned from the local Git object database; development worktree changes, old build directories, and old firmware were not copied.
- Patches were reapplied through the open-source directory's overlay script, components re-resolved, and rebuilt.
- The existing local ESP-IDF 6.0.2 compiler, its Python environment, and download/build caches were used. This is therefore source and application-dependency isolation verification, not a fresh operating system test, nor proof of byte-level reproducible builds.

## Completed

- Fresh Python environment `pip check` passed.
- Reporter: 66 tests, 53 passed, 13 skipped; exit code 0.
- Reporter EXE repackaged successfully; self-test exits 0 with a temporary config directory and no Python on PATH.
- Firmware built successfully from the locked commit, 3,762,016-byte application, fitting partition capacity.
- Single-turn conversation and quota display host tests passed; tests use the new firmware source path.
- Installer source: 11 tests passed.
- Standalone installer repackaged successfully; after removing Python/IDF paths and forcing a non-UTF-8 environment, the file manifest, backend, esptool, Reporter mode, and localized-path completion protocol self-tests all passed; exit code 0.

Firmware SHA256: `e649f596410ecca44c1fcf6716871c0447b7c7e9e3f5b78a848fbbc1bc5cfcc6`.

Reporter SHA256: `8254e77e946824342416750a66b8bba17df608f7dd620be01a784d636c89f0d2`.

Final installer self-test and SHA256 are in the same-directory completion record `BUILD_VALIDATION.json`. The exact dependency manifest is in `release/build-info/windows-validation-20260916/`, recording this build; the Windows dependency snapshot should not be used directly for Mac.

## Limitations

These are new build artifacts; they have not been installed, flashed, or voice-validated. Old artifacts' on-device acceptance cannot substitute for this batch's acceptance; another Windows machine, first-time install clearing flow, and the latest Mac version remain to be validated.

Later third-party review found that the original packer omitted some licenses; the packaging script has been corrected. The hashes in this record still correspond to the pre-correction verification artifacts; official release must rebuild and update the verification record, see THIRD_PARTY_AUDIT.md.

Repackaging has since completed: new artifacts and embedded license file verification are in RELEASE_CANDIDATE.json / RELEASE_CANDIDATE.md. This page and BUILD_VALIDATION.json retain the initial rebuild history and are not the checksum values for the latest candidate package.

PowerShell 5 records normal build output from some native programs' stderr as NativeCommandError, and the outer command may return 1. This firmware is judged on ESP-IDF's full successful build record, absence of FAILED build nodes, the actual generated application, and partition checks. Later automation should use subprocess or explicitly propagate native exit codes, rather than relying only on outer PowerShell logs.
