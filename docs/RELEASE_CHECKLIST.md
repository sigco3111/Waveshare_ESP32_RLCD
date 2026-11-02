# 1.0.0 release checklist

This file records the acceptance scope; a successful build is not treated as all functions being tested on real hardware.

## Validation already done in the development environment

- Reporter installation via the Windows standalone installer: user confirmed success.
- Configuration-preserving flashing via the Windows standalone installer: user confirmed success.
- Firmware full backup, read-back verification, and configuration-preservation check outside the application write range passed.
- Installer Chinese JSON protocol fix, 11 source checks, and standalone EXE self-test passed.
- Single-turn firmware build and playback-completion logic host tests passed; flashed to the device.

## Still to complete before official release

- [x] Independent source copy and fresh Python environment rebuild of Reporter, firmware, and installer, without reusing old binaries; compiler still uses local ESP-IDF 6.0.2; details in BUILD_VALIDATION.md.
- [ ] Voice real test: one round ends back to standby, wake again, not interrupted during playback.
- [x] 2026-10-28 independent full BIN first-time clearing install succeeded, 16 MB read-back consistent, user confirmed success (not equivalent to installer first-time install mode re-verification).
- [ ] Verify standalone installer run and installation on another Windows computer.
- [ ] Item-by-item verification of final distribution package third-party licenses, model sources, Qt corresponding source acquisition, and rebuild instructions.
  Actual dependency inventory, model hashes, Qt attribution, collection of 42 source packages, and repackaging after license completion are done; all 444 embedded license materials in both EXEs verified. Recombination testing after modifying Qt and author-applicable runtime licensing remain to be verified; see RELEASE_CANDIDATE.md.
- [ ] Secret, configuration, private log, and device image checks on Git content to be officially uploaded.
- [ ] Determine Mac release scope for this release; do not describe an old Mac package as this round's latest firmware.
- [ ] Bind final binaries and source commit, regenerate hashes and release signatures.

## Known limitations

- Music progress is current logic estimation; strict synchronization with the player is not guaranteed.
- One question per wake still depends on server-side utterance segmentation; noisy-environment performance remains to be tested.
- No Windows code signing or Mac notarization performed; state this clearly at release.
- Simulator scripts and some host tests still contain author environment path defaults; configuration or later porting is needed.
- The 2026-09-16 final candidate package completed local Reporter installation and configuration-preserving upgrade: independent re-verification of 16 MB backup, full firmware read-back, unchanged data outside the application write range, and installed Reporter hash all passed. The user confirmed normal screen light-up, automatic network connection, preserved computer binding, and continuous performance data refresh. Evidence in HARDWARE_ACCEPTANCE.json; voice, first-time clearing install, and another Windows acceptance remain.

Test reports should state system, hardware, source commit, and build artifact hashes; do not publish full Flash, account information, or raw device logs.
